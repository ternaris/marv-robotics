# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import datetime
import json
import os
import re
import sys
import warnings
from logging import getLogger

import click
from sqlalchemy.orm.exc import NoResultFound

import marv.app
from marv.config import ConfigError
from marv.model import Comment, Dataset, User, Group, dataset_tag, db
from marv.model import STATUS_MISSING
from marv.site import Site, UnknownNode
from marv.utils import find_obj
from marv_cli import marv as marvcli
from marv_cli import IPDB
from marv_node.setid import SetID
from marv_store import DirectoryAlreadyExists


log = getLogger(__name__)
warnings.simplefilter('always', DeprecationWarning)


class NodeParamType(click.ParamType):
    name = 'NODE'

    def convert(self, value, param, ctx):
        return find_obj(value)

NODE = NodeParamType()


def create_app(push=True, init=None):
    ctx = click.get_current_context()
    siteconf = ctx.obj
    if siteconf is None:
        ctx.fail('Could not find config file: ./marv.conf or /etc/marv/marv.conf.\n'
                 'Change working directory or specify explicitly:\n\n'
                 '  marv --config /path/to/marv.conf\n')
    site = Site(siteconf)
    try:
        app = marv.app.create_app(site, init=init)
    except ConfigError as e:
        click.echo('Error {}'.format(e.args[0]), err=True)
        click.get_current_context().exit(1)
    except OSError as e:
        if e.errno == 13:
            print(e, file=sys.stderr)
            sys.exit(13)
        raise
    if push:
        appctx = app.app_context()
        appctx.push()
        ctx.call_on_close(appctx.pop)
    return app


def parse_setids(datasets, discarded=False, dbids=False):
    fail = click.get_current_context().fail
    setids = set()
    for prefix in datasets:
        many = prefix.endswith('*')
        prefix = prefix[:-1] if many else prefix
        setid = db.session.query(Dataset.id if dbids else Dataset.setid)\
                          .filter(Dataset.setid.like('{}%'.format(prefix)))\
                          .filter(Dataset.discarded.is_(discarded))\
                          .all()
        if len(setid) == 0:
            fail('{} does not match any {}dataset'
                 .format(prefix, 'discarded ' if discarded else ''))
        elif len(setid) > 1 and not many:
            matches = '\n  '.join([x[0] for x in setid])
            fail("{} matches multiple:\n  {}\nUse '{}*' to mean all these."
                 .format(prefix, matches, prefix))
        setids.update(x[0] for x in setid)
        # TODO: complain about multiple
    return sorted(setids)


@marvcli.command('cleanup')
@click.option('--discarded/--no-discarded', help='Delete discarded datasets')
@click.option('--unused-tags/--no-unused-tags',
              help='Cleanup unused tags and other relations')
@click.pass_context
def marvcli_cleanup(ctx, discarded, unused_tags):
    """Cleanup unused tags and discarded datasets."""
    if not any([discarded, unused_tags]):
        click.echo(ctx.get_help())
        ctx.exit(1)

    site = create_app().site

    if discarded:
        site.cleanup_discarded()

    if unused_tags:
        site.cleanup_tags()
        site.cleanup_relations()

    # TODO: cleanup unused store paths / unused generations


@marvcli.group('develop')
def marvcli_develop():
    """Development tools."""


@marvcli_develop.command('server')
@click.option('--port', default=5000, help='Port to listen on')
@click.option('--public/--no-public',
              help='Listen on all IPs instead of only 127.0.0.1')
def marvcli_develop_server(port, public):
    """Run development webserver.

    ATTENTION: By default it is only served on localhost. To run it
    within a container and access it from the outside, you need to
    forward the port and tell it to listen on all IPs instead of only
    localhost.
    """
    from flask_cors import CORS
    app = create_app(push=False)
    app.site.load_for_web()
    CORS(app)

    class IPDBMiddleware(object):
        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
            from ipdb import launch_ipdb_on_exception
            with launch_ipdb_on_exception():
                appiter = self.app(environ, start_response)
                for item in appiter:
                    yield item

    app.debug = True
    if IPDB:
        app.wsgi_app = IPDBMiddleware(app.wsgi_app)
        app.run(use_debugger=False,
                use_reloader=False,
                host=('0.0.0.0' if public else '127.0.0.1'),
                port=port,
                threaded=False)
    else:
        app.run(host=('0.0.0.0' if public else '127.0.0.1'),
                port=port,
                reloader_type='watchdog',
                threaded=False)


@marvcli.command('discard')
@click.option('--node', 'nodes', multiple=True, help='TODO: Discard output of selected nodes')
@click.option('--all-nodes', help='TODO: Discard output of all nodes')
@click.option('--comments/--no-comments', help='Delete comments')
@click.option('--tags/--no-tags', help='Delete tags')
@click.option('--confirm/--no-confirm', default=True, show_default=True,
              help='Ask for confirmation before deleting tags and comments')
@click.argument('datasets', nargs=-1, required=True)
def marvcli_discard(datasets, all_nodes, nodes, tags, comments, confirm):
    """Mark DATASETS to be discarded or discard associated data.

    Without any options the specified datasets are marked to be
    discarded via `marv cleanup --discarded`. Use `marv undiscard` to
    undo this operation.

    Otherwise, selected data associated with the specified datasets is
    discarded right away.
    """
    mark_discarded = not any([all_nodes, nodes, tags, comments])

    site = create_app().site
    setids = parse_setids(datasets)

    if tags or comments:
        if confirm:
            msg = ' and '.join(filter(None, ['tags' if tags else None,
                                             'comments' if comments else None]))
            click.echo('About to delete {}'.format(msg))
            click.confirm('This cannot be undone. Do you want to continue?', abort=True)

        ids = [x[0] for x in db.session.query(Dataset.id).filter(Dataset.setid.in_(setids))]
        if tags:
            where = dataset_tag.c.dataset_id.in_(ids)
            stmt = dataset_tag.delete().where(where)
            db.session.execute(stmt)

        if comments:
            comment_table = Comment.__table__
            where = comment_table.c.dataset_id.in_(ids)
            stmt = comment_table.delete().where(where)
            db.session.execute(stmt)

    if nodes or all_nodes:
        storedir = site.config.marv.storedir
        for setid in setids:
            setdir = os.path.join(storedir, setid)
        # TODO: see where we are getting with dep tree tables

    if mark_discarded:
        dataset = Dataset.__table__
        stmt = dataset.update()\
                      .where(dataset.c.setid.in_(setids))\
                      .values(discarded=True)
        db.session.execute(stmt)

    db.session.commit()


@marvcli.command('undiscard')
@click.argument('datasets', nargs=-1, required=True)
def marvcli_undiscard(datasets):
    """Undiscard DATASETS previously discarded."""
    create_app()

    setids = parse_setids(datasets, discarded=True)
    dataset = Dataset.__table__
    stmt = dataset.update()\
                  .where(dataset.c.setid.in_(setids))\
                  .values(discarded=False)
    db.session.execute(stmt)
    db.session.commit()


@marvcli.command('restore')
@click.argument('file', type=click.File(), default='-')
def marvcli_restore(file):
    """Restore previously dumped database"""
    data = json.load(file)
    site = create_app().site
    site.restore_database(**data)


@marvcli.command('init')
def marvcli_init():
    """(Re-)initialize marv site according to config"""
    create_app(init=True)


@marvcli.command('query')
@click.option('--list-tags', is_flag=True, help='List all tags')
@click.option('--col', '--collection', 'collections', multiple=True,
              help='Limit to one or more collections or force listing of all with --collection=*')
@click.option('--discarded/--no-discarded', help='Dataset is discarded')
@click.option('--outdated', is_flag=True, help='Datasets with outdated node output')
@click.option('--path', type=click.Path(resolve_path=True),
              help='Dataset contains files whose path starts with PATH')
@click.option('--tagged', 'tags', multiple=True, help='Match any given tag')
@click.option('-0', '--null', is_flag=True, help='Use null byte to separate output instead of newlines')
@click.pass_context
def marvcli_query(ctx, list_tags, collections, discarded, outdated, path, tags, null):
    """Query datasets.

    Use --collection=* to list all datasets across all collections.
    """
    if not any([collections, discarded, list_tags, outdated, path, tags]):
        click.echo(ctx.get_help())
        ctx.exit(1)

    sep = '\x00' if null else '\n'

    site = create_app().site

    if '*' in collections:
        collections = None
    else:
        for col in collections:
            if col not in site.collections:
                ctx.fail('Unknown collection: {}'.format(col))

    if list_tags:
        tags = site.listtags(collections)
        if tags:
            click.echo(sep.join(tags), nl=not null)
        else:
            click.echo('no tags', err=True)
        return

    setids = site.query(collections, discarded, outdated, path, tags)
    if setids:
        sep = '\x00' if null else '\n'
        click.echo(sep.join(setids), nl=not null)


@marvcli.command('run', short_help='Run nodes for DATASETS')
@click.option('--node', 'selected_nodes', multiple=True,
              help='Run individual nodes instead of all nodes used by detail and listing'
              ' Use --list-nodes for a list of known nodes. Beyond that any node can be run'
              ' by referencing it with package.module:node')
@click.option('--list-nodes', is_flag=True, help='List known nodes instead of running')
@click.option('--list-dependent', is_flag=True, help='List nodes depending on selected nodes')
@click.option('--deps/--no-deps', default=True, show_default=True,
              help='Run dependencies of requested nodes')
@click.option('--exclude', 'excluded_nodes', multiple=True,
              help='Exclude individual nodes instead of running all nodes used by detail and listing')
@click.option('-f', '--force/--no-force',
              help='Force run of nodes whose output is already available from store')
# TODO: force-deps is bad as it does not allow to resume
# better: discard nodes selectively or discard --deps node
# discarding does not delete, but simply registers the most recent generation to be empty
@click.option('--force-deps/--no-force-deps',
              help='Force run of dependencies whose output is already available from store')
@click.option('--force-dependent/--no-force-dependent',
              help='Force run of all nodes depending on selected nodes, directly or indirectly')
@click.option('--keep/--no-keep', help='Keep uncommitted streams for debugging')
@click.option('--keep-going/--no-keep-going',
              help='In case of an exception keep going with remaining datasets')
@click.option('--detail/--no-detail', 'update_detail',
              help='Update detail view from stored node output')
@click.option('--listing/--no-listing', 'update_listing',
              help='Update listing view from stored node output')
@click.option('--cachesize', default=50, show_default=True,
              help='Number of messages to keep in memory for each stream')
@click.option('--col', '--collection', 'collections', multiple=True,
              help='Run nodes for all datasets of selected collections, use "*" for all')
@click.argument('datasets', nargs=-1)
@click.pass_context
def marvcli_run(ctx, datasets, deps, excluded_nodes, force, force_dependent,
                force_deps, keep, keep_going, list_nodes,
                list_dependent, selected_nodes, update_detail,
                update_listing, cachesize, collections):
    """Run nodes for selected datasets.

    Datasets are specified by a list of set ids, or --collection
    <name>, use --collection=* to run for all collections. --node in
    conjunction with --collection=* will pick those collections for
    which the selected nodes are configured.

    Set ids may be abbreviated to any uniquely identifying
    prefix. Suffix a prefix by '+' to match multiple.

    """
    if collections and datasets:
        ctx.fail('--collection and DATASETS are mutually exclusive')

    if list_dependent and not selected_nodes:
        ctx.fail('--list-dependent needs at least one selected --node')

    if not any([datasets, collections, list_nodes]):
        click.echo(ctx.get_help())
        ctx.exit(1)

    deps = 'force' if force_deps else deps
    force = force_deps or force

    site = create_app().site

    if '*' in collections:
        if selected_nodes:
            collections = [k for k, v in site.collections.items()
                           if set(v.nodes).issuperset(selected_nodes)]
            if not collections:
                ctx.fail('No collections have all selected nodes')
        else:
            collections = None
    else:
        for col in collections:
            if col not in site.collections:
                ctx.fail('Unknown collection: {}'.format(col))

    if list_nodes:
        for col in (collections or sorted(site.collections.keys())):
            click.echo('{}:'.format(col))
            for name in sorted(site.collections[col].nodes):
                if name == 'dataset':
                    continue
                click.echo('    {}'.format(name))
        return

    if list_dependent:
        for col in (collections or sorted(site.collections.keys())):
            click.echo('{}:'.format(col))
            dependent = {x for name in selected_nodes
                         for x in site.collections[col].nodes[name].dependent}
            for name in sorted(x.name for x in dependent):
                click.echo('    {}'.format(name))
        return

    errors = []

    setids = [SetID(x) for x in parse_setids(datasets)]
    if not setids:
        query = db.session.query(Dataset.setid)\
                           .filter(Dataset.discarded.isnot(True))\
                           .filter(Dataset.status.op('&')(STATUS_MISSING) == 0)
        if collections is not None:
            query = query.filter(Dataset.collection.in_(collections))
        setids = (SetID(x[0]) for x in query)

    for setid in setids:
        if IPDB:
            site.run(setid, selected_nodes, deps, force, keep,
                     force_dependent, update_detail, update_listing,
                     excluded_nodes, cachesize=cachesize)
        else:
            try:
                site.run(setid, selected_nodes, deps, force, keep,
                         force_dependent, update_detail, update_listing,
                         excluded_nodes, cachesize=cachesize)
            except UnknownNode as e:
                ctx.fail('Collection {} has no node {}'.format(*e.args))
            except NoResultFound:
                click.echo('ERROR: unknown {!r}'.format(setid), err=True)
                if not keep_going:
                    raise
            except BaseException as e:
                errors.append(setid)
                if isinstance(e, KeyboardInterrupt):
                    log.warn('KeyboardInterrupt: aborting')
                    raise
                elif isinstance(e, DirectoryAlreadyExists):
                    click.echo("""
ERROR: Directory for node run already exists:
{!r}
In case no other node run is in progress, this is a bug which you are kindly
asked to report, providing information regarding any previous, failed node runs.
""".format(e.args[0]), err=True)
                    if not keep_going:
                        ctx.abort()
                else:
                    log.error('Exception occured for dataset %s:', setid, exc_info=True)
                    log.error('Error occured for dataset %s: %s', setid, e)
                    if not keep_going:
                        ctx.exit(1)
    if errors:
        log.error('There were errors for %r', errors)


@marvcli.command('scan')
@click.option('-n', '--dry-run', is_flag=True)
def marvcli_scan(dry_run):
    """Scan for new and changed files"""
    create_app().site.scan(dry_run)


@marvcli.command('tag')
@click.option('--add', multiple=True, help='Tags to add')
@click.option('--rm', '--remove', multiple=True, help='Tags to remove')
@click.argument('datasets', nargs=-1)
@click.pass_context
def marvcli_tag(ctx, add, remove, datasets):
    """Add or remove tags to datasets"""
    if not any([add, remove]) or not datasets:
        click.echo(ctx.get_help())
        ctx.exit(1)

    app = create_app()
    setids = parse_setids(datasets)
    app.site.tag(setids, add, remove)


@marvcli.group('comment')
def marvcli_comment():
    """Add or remove comments"""


@marvcli_comment.command('add')
@click.option('-u', '--user', prompt=True, help='Commenting user')
@click.option('-m', '--message', required=True, help='Message for the comment')
@click.argument('datasets', nargs=-1)
def marvcli_comment_add(user, message, datasets):
    """Add comment as user for one or more datasets"""
    app = create_app()
    try:
        db.session.query(User).filter(User.name==user).one()
    except NoResultFound:
        click.echo("ERROR: No such user '{}'".format(user), err=True)
        sys.exit(1)
    ids = parse_setids(datasets, dbids=True)
    app.site.comment(user, message, ids)


@marvcli_comment.command('list')
@click.argument('datasets', nargs=-1)
def marvcli_comment_list(datasets):
    """Lists comments for datasets.

    Output: setid comment_id date time author message
    """
    app = create_app()
    ids = parse_setids(datasets, dbids=True)
    comments = db.session.query(Comment)\
                         .options(db.joinedload(Comment.dataset))\
                         .filter(Comment.dataset_id.in_(ids))
    for comment in sorted(comments, key=lambda x: (x.dataset._setid, x.id)):
        print(comment.dataset.setid, comment.id,
              datetime.datetime.fromtimestamp(int(comment.time_added / 1000)),
              comment.author, repr(comment.text))


@marvcli_comment.command('rm')
@click.argument('ids', nargs=-1)
def marvcli_comment_rm(ids):
    """Remove comments.

    Remove comments by id as given in second column of: marv comment list
    """
    app = create_app()
    db.session.query(Comment)\
              .filter(Comment.id.in_(ids))\
              .delete(synchronize_session=False)
    db.session.commit()


@marvcli.group('user')
def marvcli_user():
    """Manage user accounts"""


@marvcli_user.command('add')
@click.option('--password', help='Password will be prompted')
@click.argument('username')
@click.pass_context
def marvcli_user_add(ctx, username, password):
    """Add a user"""
    if not re.match(r'[0-9a-zA-Z\-_\.@+]+$', username):
        click.echo('Invalid username: {}'.format(username), err=True)
        click.echo('Must only contain ASCII letters, numbers, dash, underscore and dot',
                   err=True)
        sys.exit(1)
    if password is None:
        password = click.prompt('Password', hide_input=True, confirmation_prompt=True)
    app = create_app()
    try:
        app.um.user_add(username, password, 'marv', '')
    except ValueError as e:
        click.echo('Error: {}'.format(e.args[0], err=True))
        sys.exit(1)


@marvcli_user.command('list')
def marvcli_user_list():
    """List existing users"""
    app = create_app()
    query = db.session.query(User).options(db.joinedload(User.groups))\
                                  .order_by(User.name)
    users = [(user.name, ', '.join(sorted(x.name for x in user.groups)))
             for user in query]
    users = [('User', 'Groups')] + users
    uwidth, gwidth = reduce(lambda (xm, ym), (x, y): (max(x, xm), max(y, ym)),
                            ((len(x), len(y)) for x, y in users))
    fmt = '{:%ds} | {}' % uwidth
    for x, y in users:
        click.echo(fmt.format(x, y))


@marvcli_user.command('pw')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True,
              help='Password will be prompted')
@click.argument('username')
@click.pass_context
def marvcli_user_pw(ctx, username, password):
    """Change password"""
    app = create_app()
    try:
        app.um.user_pw(username, password)
    except ValueError as e:
        ctx.fail(e.args[0])


@marvcli_user.command('rm')
@click.argument('username')
@click.pass_context
def marvcli_user_rm(ctx, username):
    """Remove a user"""
    app = create_app()
    try:
        app.um.user_rm(username)
    except ValueError as e:
        ctx.fail(e.args[0])


@marvcli.group('group')
def marvcli_group():
    """Manage user groups"""


@marvcli_group.command('add')
@click.argument('groupname')
@click.pass_context
def marvcli_group_add(ctx, groupname):
    """Add a group"""
    if not re.match(r'[0-9a-zA-Z\-_\.@+]+$', groupname):
        click.echo('Invalid groupname: {}'.format(groupname), err=True)
        click.echo('Must only contain ASCII letters, numbers, dash, underscore and dot',
                   err=True)
        sys.exit(1)
    app = create_app()
    try:
        app.um.group_add(groupname)
    except ValueError as e:
        ctx.fail(e.args[0])


@marvcli_group.command('list')
def marvcli_group_list():
    """List existing groups"""
    app = create_app()
    query = db.session.query(Group.name).order_by(Group.name)
    for name in [x[0] for x in query]:
        click.echo(name)


@marvcli_group.command('adduser')
@click.argument('username')
@click.argument('groupname')
@click.pass_context
def marvcli_group_adduser(ctx, groupname, username):
    """Add an user to a group"""
    app = create_app()
    try:
        app.um.group_adduser(groupname, username)
    except ValueError as e:
        ctx.fail(e.args[0])


@marvcli_group.command('rmuser')
@click.argument('username')
@click.argument('groupname')
@click.pass_context
def marvcli_group_rmuser(ctx, groupname, username):
    """Remove an user from a group"""
    app = create_app()
    try:
        app.um.group_rmuser(groupname, username)
    except ValueError as e:
        ctx.fail(e.args[0])


@marvcli_group.command('rm')
@click.argument('groupname')
@click.pass_context
def marvcli_group_rm(ctx, groupname):
    """Remove a group"""
    app = create_app()
    try:
        app.um.group_rm(groupname)
    except ValueError as e:
        ctx.fail(e.args[0])
