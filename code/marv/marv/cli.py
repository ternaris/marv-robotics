# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import asyncio
import code
import datetime
import functools
import json
import signal
import sqlite3
import sys
import traceback
from contextlib import asynccontextmanager
from functools import reduce
from logging import getLogger
from pathlib import Path
from runpy import run_path

import click
from aiohttp import web
from gunicorn.app.base import BaseApplication
from gunicorn.arbiter import Arbiter
from jinja2 import Template
from tortoise.exceptions import DoesNotExist

import marv_node.run
from marv.config import ConfigError
from marv.db import USERGROUP_REGEX, DBError, DBNotInitialized, DBPermissionError, DBVersionError
from marv.site import SiteError, load_sitepackages, make_config
from marv.utils import within_pyinstaller_bundle
from marv_api import ReaderError
from marv_api.utils import echo, err, find_obj
from marv_cli import PDB
from marv_cli import marv as marvcli
from marv_node.stream import RequestedMessageTooOld
from marv_store import DirectoryAlreadyExists

try:
    import marv_ee
except ImportError:
    marv_ee = None

if marv_ee:
    marv_ee.init()
    from marv_ee.app import App  # pylint: disable=import-error
    from marv_ee.site import Site  # pylint: disable=import-error
else:
    from marv.app import App
    from marv.site import Site

log = getLogger(__name__)


class NodeParamType(click.ParamType):
    name = 'NODE'

    def convert(self, value, param, ctx):
        return find_obj(value)


NODE = NodeParamType()


def get_site_config():
    ctx = click.get_current_context()
    siteconf = ctx.obj
    if siteconf is None:
        ctx.fail('Could not find config file: ./marv.conf or /etc/marv/marv.conf.\n'
                 'Change working directory or specify explicitly:\n\n'
                 '  marv --config /path/to/marv.conf\n')
    return siteconf


@asynccontextmanager
async def create_site(init=None):
    siteconf = get_site_config()
    try:
        site = await Site.create(siteconf, init=init)
    except (sqlite3.OperationalError, DBNotInitialized) as exc:
        if PDB:
            raise
        err(f'{exc!r}\n\nDid you run marv init?\n', exit=1)
    except DBVersionError as exc:
        err(f'{exc!r}\n\n'
            'Existing database is not compatible with this version of MARV. '
            'Check the migration instructions.', exit=1)
    except (ConfigError, SiteError) as exc:
        err(f'ERROR: {exc}', exit=1)
    try:
        yield site
    finally:
        await site.destroy()


def click_async(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper


class NoSigintArbiter(Arbiter):
    def handle_int(self):
        signal.signal(signal.SIGINT, lambda *_: self.kill_workers(signal.SIGKILL))
        super().handle_term()


class GunicornApplication(BaseApplication):  # pylint: disable=abstract-method
    def __init__(self, app_factory, bind, certfile, keyfile, *args, **kw):
        # pylint: disable=too-many-arguments
        self.app_factory = app_factory
        self.bind = bind
        self.certfile = certfile
        self.keyfile = keyfile
        super().__init__(*args, **kw)

    def load_config(self):
        self.cfg.set('proc_name', 'marvweb')
        self.cfg.set('worker_class', 'aiohttp.GunicornUVLoopWebWorker')
        self.cfg.set('bind', self.bind)
        self.cfg.set('certfile', self.certfile)
        self.cfg.set('keyfile', self.keyfile)
        self.cfg.set('workers', 1)
        self.cfg.set('graceful_timeout', 86400)

    def load(self):
        return self.app_factory

    def run(self):
        try:
            NoSigintArbiter(self).run()
        except RuntimeError as e:
            err(f'\nERROR: {e}', exit=1)


@marvcli.command('cleanup')
@click.option('--discarded/--no-discarded', help='Delete discarded datasets')
@click.option('--filters/--no-filters', help='Cleanup unused filter values')
@click.pass_context
@click_async
async def marvcli_cleanup(ctx, discarded, filters):
    """Cleanup subset filters and discarded datasets."""
    if not any([discarded, filters]):
        click.echo(ctx.get_help())
        ctx.exit(1)

    async with create_site() as site:
        if discarded:
            await site.cleanup_discarded()

        if filters:
            await site.cleanup_relations()

        # TODO: cleanup unused store paths / unused generations


@marvcli.group('develop')
def marvcli_develop():
    """Development tools."""


@marvcli_develop.command('server')
@click.option('--port', default=5000, help='Port to listen on')
@click.option('--public/--no-public', help='Listen on all IPs instead of only 127.0.0.1')
def marvcli_develop_server(port, public):
    """Run development webserver.

    ATTENTION: By default it is only served on localhost. To run it
    within a container and access it from the outside, you need to
    forward the port and tell it to listen on all IPs instead of only
    localhost.
    """
    middlewares = []
    if PDB:
        @web.middleware
        async def pdb_middleware(request, handler):
            try:
                return await handler(request)
            except Exception:  # pylint: disable=broad-except
                import pdb  # pylint: disable=import-outside-toplevel
                pdb.xpm()  # pylint: disable=no-member

        middlewares.append(pdb_middleware)

    async def create_app(middlewares=None):
        siteconf = get_site_config()
        site = await Site.create(siteconf)
        return App(site, middlewares=middlewares).aioapp

    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(create_app(middlewares=middlewares))
    app['debug'] = True
    web.run_app(app,
                host=('0.0.0.0' if public else '127.0.0.1'),
                port=port)


@marvcli.command('serve')
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=8000, help='Port to listen on')
@click.option('--certfile', default=None, help='SSL certificate')
@click.option('--keyfile', default=None, help='SSL keyfile')
@click.option('--approot', default='/', help='Application root to serve', show_default=True)
def marvcli_serve(host, port, certfile, keyfile, approot):
    """Run webserver through gunicorn."""
    config = get_site_config()
    if within_pyinstaller_bundle():
        ensure_python(config, '')

    async def app_factory():
        """App factory used inside of worker.

        Note:
            Terminates execution via sys.exit(4) to prevent master from restarting worker.

        """
        try:
            site = await Site.create(config)
            try:
                application = App(site, app_root=approot).aioapp
            except Exception:  # pylint: disable=broad-except
                await site.destroy()
                raise
        except (sqlite3.OperationalError, DBNotInitialized) as exc:
            err(f'{exc!r}\nDid you run marv init?', exit=4)
        except DBVersionError as exc:
            err(f'{exc!r}\n'
                'Existing database is not compatible with this version of MARV. '
                'Check the migration instructions.', exit=4)
        except (PermissionError, SiteError) as exc:
            err(f'ERROR: {exc}', exit=4)
        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()
            sys.exit(4)
        return application

    GunicornApplication(app_factory, f'{host}:{port}', certfile, keyfile).run()


@marvcli.command('discard')
@click.option(
    '--comments/--no-comments',
    help='Delete comments',
)
@click.option(
    '--tags/--no-tags',
    help='Delete tags',
)
@click.option(
    '--confirm/--no-confirm', default=True, show_default=True,
    help='Ask for confirmation before deleting tags and comments',
)
@click.argument('datasets', nargs=-1, required=True)
@click_async
async def marvcli_discard(datasets, tags, comments, confirm):
    """Mark DATASETS to be discarded or discard associated data.

    Without any options the specified datasets are marked to be
    discarded via `marv cleanup --discarded`. Use `marv undiscard` to
    undo this operation.

    Otherwise, selected data associated with the specified datasets is
    discarded right away.
    """
    delete_related = list(filter(None, [
        'comments' if comments else None,
        'tags' if tags else None,
    ]))
    if delete_related and confirm:
        msg = ''.join(f'  - {x}\n' for x in delete_related)
        click.confirm(f'About to PERMANENTLY delete:\n{msg}Do you want to continue?', abort=True)

    async with create_site() as site:
        if delete_related:
            await site.db.delete_comments_tags(datasets, comments, tags)
        else:
            await site.db.discard_datasets_by_setids(datasets)


@marvcli.command('undiscard')
@click.argument('datasets', nargs=-1, required=True)
@click_async
async def marvcli_undiscard(datasets):
    """Undiscard DATASETS previously discarded."""
    async with create_site() as site:
        await site.db.discard_datasets_by_setids(datasets, False)


@marvcli.command('dump')
@click.argument('dump_file', type=Path)
@click_async
async def marvcli_dump(dump_file):
    """Dump database to json file.

    Use '-' for stdout.
    """
    if str(dump_file) != '-' and dump_file.exists():
        err('ERROR: Dump file must not exist already!', exit=1)

    siteconf = make_config(get_site_config())
    try:
        dump = await Site.Database.dump_database(siteconf.marv.dburi)
    except DBNotInitialized as exc:
        err(f'ERROR: {exc}', exit=1)
    except DBVersionError as exc:
        err(f'ERROR: {exc} Please use the correct version of marv to dump.', exit=1)

    if str(dump_file) == '-':
        json.dump(dump, sys.stdout, sort_keys=True, indent=2)
    else:
        with dump_file.open('w') as f:
            json.dump(dump, f, sort_keys=True, indent=2)


@marvcli.command('restore')
@click.argument('dump_file', type=click.File())
@click_async
async def marvcli_restore(dump_file):
    """Restore previously dumped database from file.

    Use '-' to read from stdin.
    """
    data = json.load(dump_file)

    async with create_site() as site:
        await site.restore_database(**data)


@marvcli.command('init')
@click_async
async def marvcli_init():
    """(Re-)initialize marv site according to config."""
    async with create_site(init=True):
        pass


@marvcli.command('query')
@click.option(
    '--list-tags', is_flag=True,
    help='List all tags',
)
@click.option(
    '--col', '--collection', 'collections', multiple=True,
    help='Limit to one or more collections or force listing of all with --collection=*',
)
@click.option(
    '--discarded/--no-discarded',
    help='Dataset is discarded',
)
@click.option(
    '--missing', is_flag=True,
    help='Datasets with missing files',
)
@click.option(
    '--outdated', is_flag=True,
    help='Datasets with outdated node output',
)
@click.option(
    '--path', type=click.Path(resolve_path=True),
    help='Dataset contains files whose path starts with PATH',
)
@click.option(
    '--tagged', 'tags', multiple=True,
    help='Match any given tag',
)
@click.option(
    '-0', '--null', is_flag=True,
    help='Use null byte to separate output instead of newlines',
)
@click.pass_context
@click_async
async def marvcli_query(ctx, list_tags, collections, discarded,
                        missing, outdated, path, tags, null):
    """Query datasets.

    Use --col=* to list all datasets across all collections.
    """
    # pylint: disable=too-many-arguments

    if not any([collections, discarded, list_tags, missing, outdated, path, tags]):
        click.echo(ctx.get_help())
        ctx.exit(1)

    sep = '\x00' if null else '\n'

    async with create_site() as site:
        if '*' in collections:
            collections = None
        else:
            for col in collections:
                if col not in site.collections:
                    ctx.fail(f'Unknown collection: {col}')

        if list_tags:
            tags = await site.db.list_tags(collections)
            if tags:
                click.echo(sep.join(tags), nl=not null)
            return

        setids = await site.db.query(collections, discarded, outdated, path, tags, missing=missing)
        if setids:
            sep = '\x00' if null else '\n'
            click.echo(sep.join(str(x) for x in setids), nl=not null)


@marvcli.command('run', short_help='Run nodes for DATASETS')
@click.option(
    '--node', 'selected_nodes', multiple=True,
    help=(
        'Run individual nodes instead of all nodes used by detail and listing '
        'Use --list-nodes for a list of known nodes. Beyond that any node can be run '
        'by referencing it with package.module:node'
    ),
)
@click.option(
    '--list-nodes', is_flag=True,
    help='List known nodes instead of running',
)
@click.option(
    '--list-dependent', is_flag=True,
    help='List nodes depending on selected nodes',
)
@click.option(
    '--deps/--no-deps', default=True, show_default=True,
    help='Run dependencies of requested nodes',
)
@click.option(
    '--exclude', 'excluded_nodes', multiple=True,
    help='Exclude individual nodes instead of running all nodes used by detail and listing',
)
@click.option(
    '-f', '--force/--no-force',
    help='Force run of nodes whose output is already available from store',
)
# TODO: force-deps is bad as it does not allow to resume
# better: discard nodes selectively or discard --deps node
# discarding does not delete, but simply registers the most recent generation to be empty
@click.option(
    '--force-deps/--no-force-deps',
    help='Force run of dependencies whose output is already available from store',
)
@click.option(
    '--force-dependent/--no-force-dependent',
    help='Force run of all nodes depending on selected nodes, directly or indirectly',
)
@click.option('--keep/--no-keep', help='Keep uncommitted streams for debugging')
@click.option(
    '--keep-going/--no-keep-going',
    help='In case of an exception keep going with remaining datasets',
)
@click.option(
    '--detail/--no-detail', 'update_detail',
    help='Update detail view from stored node output',
)
@click.option(
    '--listing/--no-listing', 'update_listing',
    help='Update listing view from stored node output',
)
@click.option(
    '--cachesize', default=50, show_default=True,
    help='Number of messages to keep in memory for each stream',
)
@click.option(
    '--col', '--collection', 'collections', multiple=True,
    help='Run nodes for all datasets of selected collections, use "*" for all',
)
@click.argument('datasets', nargs=-1)
@click.pass_context
@click_async
async def marvcli_run(  # noqa: C901
        ctx, datasets, deps, excluded_nodes, force, force_dependent, force_deps, keep, keep_going,
        list_nodes, list_dependent, selected_nodes, update_detail, update_listing, cachesize,
        collections,
):
    """Run nodes for selected datasets.

    Datasets are specified by a list of set ids, or --collection
    <name>, use --collection=* to run for all collections. --node in
    conjunction with --collection=* will pick those collections for
    which the selected nodes are configured.

    Set ids may be abbreviated to any uniquely identifying
    prefix.
    """
    # pylint: disable=too-many-arguments,too-many-locals,too-many-branches,too-many-statements

    if collections and datasets:
        ctx.fail('--collection and DATASETS are mutually exclusive')

    if list_dependent and not selected_nodes:
        ctx.fail('--list-dependent needs at least one selected --node')

    if force_dependent and not selected_nodes:
        ctx.fail('--force-dependent needs at least one selected --node')

    if not any([datasets, collections, list_nodes]):
        click.echo(ctx.get_help())
        ctx.exit(1)

    deps = 'force' if force_deps else deps
    force = force_deps or force

    async with create_site() as site:
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
                    ctx.fail(f'Unknown collection: {col}')

        if list_nodes:
            for col in (collections or sorted(site.collections.keys())):
                click.echo(f'{col}:')
                for name in sorted(site.collections[col].nodes):
                    if name == 'dataset':
                        continue
                    click.echo(f'    {name}')
            return

        if list_dependent:
            for col in (collections or sorted(site.collections.keys())):
                click.echo(f'{col}:')
                dependent = {x for name in selected_nodes
                             for x in site.collections[col].nodes[name].dependent}
                for name in sorted(x.name for x in dependent):
                    click.echo(f'    {name}')
            return

        errors = []
        if datasets:
            setids = datasets
        else:
            setids = await site.db.get_datasets_for_collections(collections)

        if not PDB:
            # TODO: Move signal handling into runner
            def handle_abort(_1, _2):
                marv_node.run.setabort()

            signal.signal(signal.SIGINT, handle_abort)
            signal.signal(signal.SIGTERM, handle_abort)

        for setid in setids:
            if PDB:
                await site.run(setid, selected_nodes, deps, force, keep,
                               force_dependent, update_detail, update_listing,
                               excluded_nodes, cachesize=cachesize)
            else:
                try:
                    await site.run(setid, selected_nodes, deps, force, keep,
                                   force_dependent, update_detail, update_listing,
                                   excluded_nodes, cachesize=cachesize)
                except ConfigError as exc:
                    err(f'ERROR: {exc}', exit=1)
                except DoesNotExist:
                    click.echo(f'ERROR: unknown {setid!r}', err=True)
                    if not keep_going:
                        raise
                except RequestedMessageTooOld as e:
                    _req = e.args[0]._requestor.node.name  # pylint: disable=no-member,protected-access
                    _handle = e.args[0].handle.node.name  # pylint: disable=no-member
                    click.echo(f"""
    ERROR: {_req} pulled {_handle} message {e.args[1]} not being in memory anymore.
    See https://ternaris.com/marv-robotics/docs/patterns.html#reduce-separately
    """, err=True)
                    ctx.abort()
                except marv_node.run.Aborted:
                    ctx.abort()
                except ReaderError as e:
                    errors.append(setid)
                    log.error('Reader error for dataset %s: %s', setid, e)
                except Exception as e:  # pylint: disable=broad-except
                    errors.append(setid)
                    if isinstance(e, DirectoryAlreadyExists):
                        click.echo(f"""
    ERROR: Directory for node run already exists:
    {e.args[0]!r}
    In case no other node run is in progress, this is a bug which you are kindly
    asked to report, providing information regarding any previous, failed node runs.
    """, err=True)
                        if not keep_going:
                            ctx.abort()
                    else:
                        log.error('Exception occurred for dataset %s:', setid, exc_info=True)
                        log.error('Error occurred for dataset %s: %s', setid, e)
                        if not keep_going:
                            ctx.exit(1)
        if errors:
            log.error('There were errors for %r', errors)


@marvcli.command('scan')
@click.option('-n', '--dry-run', is_flag=True)
@click_async
async def marvcli_scan(dry_run):
    """Scan for new and changed files."""
    async with create_site() as site:
        try:
            await site.scan(dry_run)
        except ConfigError as exc:
            err(f'ERROR: {exc}', exit=1)


@marvcli.command('tag')
@click.option('--add', multiple=True, help='Tags to add')
@click.option('--rm', '--remove', 'remove', multiple=True, help='Tags to remove')
@click.option(
    '--strict',
    is_flag=True,
    help=('By default tagging via CLI is idempotent; in strict mode it will fail if tags'
          ' are repeatedly added or removed.'),
)
@click.argument('datasets', nargs=-1)
@click.pass_context
@click_async
async def marvcli_tag(ctx, add, remove, strict, datasets):
    """Add or remove tags to datasets."""
    if not any([add, remove]) or not datasets:
        click.echo(ctx.get_help())
        ctx.exit(1)

    async with create_site() as site:
        try:
            await site.db.update_tags_by_setids(datasets, add, remove, idempotent=not strict)
        except DBPermissionError:
            if strict:
                err('ERROR: --strict prevented add of existing or remove of non-existing tag(s).',
                    exit=1)
            raise


@marvcli.group('comment')
def marvcli_comment():
    """Add or remove comments."""


@marvcli_comment.command('add')
@click.option('-u', '--user', prompt=True, help='Commenting user')
@click.option('-m', '--message', required=True, help='Message for the comment')
@click.argument('datasets', nargs=-1)
@click_async
async def marvcli_comment_add(user, message, datasets):
    """Add comment as user for one or more datasets."""
    async with create_site() as site:
        try:
            await site.db.comment_by_setids(datasets, user, message)
        except DBError as e:
            err(f'ERROR: {e}', exit=1)


@marvcli_comment.command('list')
@click.argument('datasets', nargs=-1)
@click_async
async def marvcli_comment_list(datasets):
    """List comments for datasets.

    Output: setid comment_id date time author message
    """
    async with create_site() as site:
        comments = await site.db.get_comments_by_setids(datasets)
        for comment in sorted(comments, key=lambda x: (x.dataset[0].setid, x.id)):
            echo(comment.dataset[0].setid, comment.id,
                 datetime.datetime.fromtimestamp(int(comment.time_added / 1000)),  # noqa: DTZ
                 comment.author, repr(comment.text))


SHOW_TEMPLATE = Template("""
{% for dataset in datasets %}
- name: {{ dataset.name }}
  collection: {{ dataset.collection }}
  setid: {{ dataset.setid }}
  files:
  {% for file in dataset.files %}
    - path: {{ file.path }}
      size: {{ file.size }}
  {% endfor %}

{% endfor %}
""".strip(), trim_blocks=True, lstrip_blocks=True)


@marvcli.command('show')
@click.argument('datasets', nargs=-1, required=True)
@click_async
async def marvcli_show(datasets):
    """Show information for one or more datasets in form of a yaml document.

    Set ids may be abbreviated as long as they are unique.

    \b
    Some examples
      marv show setid  # show one dataset
      marv query --col=* | xargs marv show   # show all datasets
    """
    async with create_site() as site:
        datasets = await site.db.get_datasets_by_setids(datasets, prefetch=['files'], user='::')
        yamldoc = SHOW_TEMPLATE.render(datasets=datasets)
        echo(yamldoc, end='')


@marvcli_comment.command('rm')
@click.argument('ids', nargs=-1)
@click_async
async def marvcli_comment_rm(ids):
    """Remove comments.

    Remove comments by id as given in second column of: marv comment list
    """
    async with create_site() as site:
        await site.db.delete_comments_by_ids(ids)


@marvcli.group('user')
def marvcli_user():
    """Manage user accounts."""


@marvcli_user.command('add')
@click.option('--password', help='Password will be prompted')
@click.argument('username')
@click_async
async def marvcli_user_add(username, password):
    """Add a user."""
    if not USERGROUP_REGEX.match(username):
        click.echo(f'Invalid username: {username}', err=True)
        click.echo('Must only contain ASCII letters, numbers, and [-_+@.]', err=True)
        sys.exit(1)

    if password is None:
        password = click.prompt('Password', hide_input=True, confirmation_prompt=True)

    async with create_site() as site:
        try:
            await site.db.user_add(username, password, 'marv', '')
        except ValueError as e:
            click.echo(f'Error: {e.args[0]}', err=True)
            sys.exit(1)


@marvcli_user.command('list')
@click_async
async def marvcli_user_list():
    """List existing users."""
    async with create_site() as site:
        query = await site.db.get_users(deep=True)
        users = [(user.name, ', '.join(sorted(x.name for x in user.groups))) for user in query]
        users = [('User', 'Groups')] + users
        uwidth, _ = reduce(
            lambda xm_ym, x_y: (max(x_y[0], xm_ym[0]), max(x_y[1], xm_ym[1])),
            ((len(x), len(y)) for x, y in users),
        )
        fmt = '{:%ds} | {}' % uwidth
        for user, groups in users:
            click.echo(fmt.format(user, groups))


@marvcli_user.command('pw')
@click.option(
    '--password', prompt=True, hide_input=True, confirmation_prompt=True,
    help='Password will be prompted',
)
@click.argument('username')
@click.pass_context
@click_async
async def marvcli_user_pw(ctx, username, password):
    """Change password."""
    async with create_site() as site:
        try:
            await site.db.user_pw(username, password)
        except ValueError as e:
            ctx.fail(e.args[0])


@marvcli_user.command('rm')
@click.argument('username')
@click.pass_context
@click_async
async def marvcli_user_rm(ctx, username):
    """Remove a user."""
    async with create_site() as site:
        try:
            await site.db.user_rm(username)
        except ValueError as e:
            ctx.fail(e.args[0])


@marvcli.group('group')
def marvcli_group():
    """Manage user groups."""


@marvcli_group.command('add')
@click.argument('groupname')
@click.pass_context
@click_async
async def marvcli_group_add(ctx, groupname):
    """Add a group."""
    if not USERGROUP_REGEX.match(groupname):
        click.echo(f'Invalid groupname: {groupname}', err=True)
        click.echo('Must only contain ASCII letters, numbers, dash, underscore and dot', err=True)
        sys.exit(1)

    async with create_site() as site:
        try:
            await site.db.group_add(groupname)
        except ValueError as e:
            ctx.fail(e.args[0])


@marvcli_group.command('list')
@click_async
async def marvcli_group_list():
    """List existing groups."""
    async with create_site() as site:
        for group in await site.db.get_groups():
            click.echo(group.name)


@marvcli_group.command('adduser')
@click.argument('username')
@click.argument('groupname')
@click.pass_context
@click_async
async def marvcli_group_adduser(ctx, groupname, username):
    """Add an user to a group."""
    async with create_site() as site:
        try:
            await site.db.group_adduser(groupname, username)
        except ValueError as e:
            ctx.fail(e.args[0])


@marvcli_group.command('rmuser')
@click.argument('username')
@click.argument('groupname')
@click.pass_context
@click_async
async def marvcli_group_rmuser(ctx, groupname, username):
    """Remove an user from a group."""
    async with create_site() as site:
        try:
            await site.db.group_rmuser(groupname, username)
        except ValueError as e:
            ctx.fail(e.args[0])


@marvcli_group.command('rm')
@click.argument('groupname')
@click.pass_context
@click_async
async def marvcli_group_rm(ctx, groupname):
    """Remove a group."""
    async with create_site() as site:
        try:
            await site.db.group_rm(groupname)
        except ValueError as e:
            ctx.fail(e.args[0])


@marvcli.group('pip', hidden=not marv_ee)
def marvcli_pip():
    """Integrate pip commands (EE)."""


def ensure_python(siteconf, sitepackages):
    assert within_pyinstaller_bundle()
    pyexe = Path(code.__file__).parent / 'python'
    if not pyexe.exists():
        with pyexe.open('w') as f:
            f.write(f'#!/bin/sh\n'
                    f'export PYTHONPATH="{sitepackages}:$PYTHONPATH"\n'
                    f'exec {sys.executable} --config {siteconf} python "$@"')
        pyexe.chmod(0o700)
    sys.executable = str(pyexe)


@marvcli_pip.command('install', context_settings={'ignore_unknown_options': True})
@click.argument('pipargs', nargs=-1, type=click.UNPROCESSED)
def marvcli_pip_install(pipargs):
    """Install python package (EE).

    Use -e like with plain pip to install in editable mode.
    """
    assert within_pyinstaller_bundle()
    siteconf = get_site_config()
    config = make_config(siteconf)
    sitepackages = config.marv.sitepackages
    load_sitepackages(sitepackages)
    ensure_python(siteconf, sitepackages)
    from pip._internal.main import main as pip_main  # pylint: disable=import-outside-toplevel
    sys.argv = [sys.executable, 'install', '--prefix', str(config.marv.venv), *pipargs]
    sys.exit(pip_main())


@marvcli_pip.command('uninstall', context_settings={'ignore_unknown_options': True})
@click.argument('pipargs', nargs=-1, type=click.UNPROCESSED)
def marvcli_pip_uninstall(pipargs):
    """Uninstall python package (EE)."""
    assert within_pyinstaller_bundle()
    siteconf = get_site_config()
    sitepackages = make_config(siteconf).marv.sitepackages
    load_sitepackages(sitepackages)
    ensure_python(siteconf, sitepackages)
    from pip._internal.main import main as pip_main  # pylint: disable=import-outside-toplevel
    sys.argv = [sys.executable, 'uninstall', *pipargs]
    sys.exit(pip_main())


@marvcli.command('python', hidden=not marv_ee, context_settings={'ignore_unknown_options': True})
@click.option('-u', '--unbuffered', is_flag=True, help='Python -u equivalent (ignored)')
@click.option('-E', 'ignore', is_flag=True, help='Python -E equivalent (ignored)')
@click.option('-c', '--command', help='Python -c equivalent')
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
def marvcli_python(unbuffered, ignore, command, args):  # pylint: disable=unused-argument
    """Drop into interactive python (EE)."""
    assert within_pyinstaller_bundle()
    siteconf = get_site_config()
    sitepackages = make_config(siteconf).marv.sitepackages
    load_sitepackages(sitepackages)
    ensure_python(siteconf, sitepackages)
    if command:
        sys.argv = ['-c', *args]
        sys.path.append('.')
        exec(compile(command, 'python_wrapper', 'exec'))  # pylint: disable=exec-used
    elif args:
        sys.argv = [*args]
        sys.path.append('.')
        run_path(args[0], run_name='__main__')
    else:
        code.interact(local=locals())
