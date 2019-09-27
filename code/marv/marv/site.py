# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import fcntl
import os
import shutil
from itertools import count, groupby, product
from logging import getLogger
from uuid import uuid4

import bcrypt
import sqlalchemy as sqla
import sqlalchemy.exc
from pkg_resources import resource_filename
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from marv_node.run import run_nodes
from marv_store import Store
from . import utils
from .collection import Collections
from .collection import esc
from .config import Config
from .model import Comment, Dataset, File, Group, Model, Tag, User, dataset_tag, scoped_session
from .model import STATUS_OUTDATED


DEFAULT_NODES = """
marv_nodes:dataset
marv_nodes:meta_table
marv_nodes:summary_keyval
"""

DEFAULT_FILTERS = """
name       | Name       | substring         | string   | (get "dataset.name")
setid      | Set Id     | startswith        | string   | (get "dataset.id")
size       | Size       | lt le eq ne ge gt | filesize | (sum (get "dataset.files[:].size"))
status     | Status     | any all           | subset   | (status )
tags       | Tags       | any all           | subset   | (tags )
comments   | Comments   | substring         | string   | (comments )
files      | File paths | substring_any     | string[] | (get "dataset.files[:].path")
time_added | Added      | lt le eq ne ge gt | datetime | (get "dataset.time_added")
"""

DEFAULT_LISTING_COLUMNS = """
name       | Name   | route    | (detail_route (get "dataset.id") (get "dataset.name"))
size       | Size   | filesize | (sum (get "dataset.files[:].size"))
status     | Status | icon[]   | (status )
tags       | Tags   | pill[]   | (tags )
time_added | Added  | datetime | (get "dataset.time_added")
"""

DEFAULT_LISTING_SUMMARY = """
datasets | datasets | int       | (len (rows ))
size     | size     | filesize  | (sum (rows "size" 0))
"""

DEFAULT_DETAIL_SUMMARY_WIDGETS = """
summary_keyval
meta_table
"""

log = getLogger(__name__)


class UnknownNode(Exception):
    pass


def make_config(siteconf):
    sitedir = os.path.dirname(siteconf)
    defaults = {
        'marv': {
            'acl': 'marv_webapi.acls:authenticated',
            'dburi': 'sqlite:///' + os.path.join(sitedir, 'db', 'db.sqlite'),
            'frontenddir': os.path.join(sitedir, 'frontend'),
            'oauth': '',
            'reverse_proxy': None,
            'sessionkey_file': os.path.join(sitedir, 'sessionkey'),
            'staticdir': os.path.join(resource_filename('marv_ludwig', 'static')),
            'storedir': os.path.join(sitedir, 'store'),
            'window_title': '',
        },
        'collection': {
            'compare': None,
            'detail_summary_widgets': DEFAULT_DETAIL_SUMMARY_WIDGETS,
            'detail_sections': '',
            'detail_title': '(get "dataset.name")',
            'filters': DEFAULT_FILTERS,
            'listing_columns': DEFAULT_LISTING_COLUMNS,
            'listing_sort': '| ascending',
            'listing_summary': DEFAULT_LISTING_SUMMARY,
            'nodes': DEFAULT_NODES,
        },
    }
    required = {
        'marv': [
            'collections',
        ],
        'collection': [
            'scanner',
            'scanroots',
        ],
    }
    schema = {
        'marv': {
            'acl': 'find_obj',
            'collections': 'space_separated_list',
            'oauth': 'lines',
            'staticdir': 'path',
            'storedir': 'path',
        },
        'collection': {
            'compare': 'find_obj',
            'detail_title': 'function',
            'detail_summary_widgets': 'lines',
            'detail_sections': 'lines',
            'filters': 'lines',
            'listing_columns': 'lines',
            'listing_sort': 'pipe_separated_list',
            'listing_summary': 'lines',
            'nodes': 'lines',
            'scanroots': 'path_lines',
        },
    }
    return Config.from_file(siteconf, defaults=defaults,
                            required=required, schema=schema)


class DBNotInitialized(Exception):
    pass


class Site:
    def __init__(self, siteconf, init=None):
        self.config = make_config(siteconf)
        # TODO: maybe ordereddict for meta, or generate multiple keys
        self.config.marv.oauth = {
            line.split(' ', 1)[0]: [field.strip() for field in line.split('|')]
            for line in self.config.marv.oauth
        }
        self.engine = create_engine(self.config.marv.dburi)
        self.session = sessionmaker(bind=self.engine)
        self.collections = Collections(config=self.config, site=self)

        with scoped_session(self) as session:
            if init:
                self.init()
            try:
                session.execute('SELECT name FROM sqlite_master WHERE type="table";')
            except sqlalchemy.exc.OperationalError:
                if init is None:  # auto-init
                    self.init()
                    session.execute('SELECT name FROM sqlite_master WHERE type="table";')
                else:
                    raise DBNotInitialized()

    def load_for_web(self):
        _ = [getattr(x, y) and None for x, y, in product(
            self.collections.values(),
            ('compare', 'filter_specs', 'listing_columns', 'model',
             'sortcolumn', 'sortorder', 'summary_items'))]

    def init(self):  # noqa: C901
        # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        try:
            fd = os.open(self.config.marv.sessionkey_file,
                         os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666)
        except OSError as e:
            if e.errno != 17:
                raise
        else:
            with os.fdopen(fd, 'w') as f:
                f.write(str(uuid4()))
            log.verbose('Generated %s', self.config.marv.sessionkey_file)

        try:
            os.mkdir(self.config.marv.storedir)
            log.verbose('Created %s', self.config.marv.storedir)
        except OSError as e:
            if e.errno != 17:
                raise

        try:
            dbdir = os.path.dirname(self.config.marv.dburi.replace('sqlite:///', ''))
            os.mkdir(dbdir)
            log.verbose('Created %s', dbdir)
        except OSError as e:
            if e.errno != 17:
                raise

        # TODO: maybe this should be an explicit method...
        # load models
        _ = [x.model for x in self.collections.values()]

        with scoped_session(self) as session:
            prefixes = [f'listing_{col}' for col in self.collections.keys()]
            result = session.execute('SELECT name FROM sqlite_master WHERE type="table";')
            tables = {name for name in [x[0] for x in result]
                      if any(name.startswith(prefix) for prefix in prefixes)}
            for table in [x for x in tables if x.endswith('_sec')]:
                session.execute(f'DROP TABLE {table};')
                tables.discard(table)
            for table in [x for x in tables if x not in prefixes]:
                session.execute(f'DROP TABLE {table};')
                tables.discard(table)
            for table in tables:
                session.execute(f'DROP TABLE {table};')

            Model.metadata.create_all(self.engine)
            for name in ('admin', ):
                if not session.query(Group).filter(Group.name == name).count():
                    session.add(Group(name=name))
                    session.commit()

            log.verbose('Initialized database %s', self.config.marv.dburi)
            for col in self.collections.keys():
                collection = self.collections[col]
                loop = count()
                batchsize = 50
                # TODO: increase verbosity and probably introduce --reinit
                while True:
                    batch = session.query(Dataset)\
                                   .filter(Dataset.collection == col)\
                                   .options(joinedload(Dataset.files))\
                                   .limit(batchsize)\
                                   .offset(batchsize*next(loop))\
                                   .all()
                    for dataset in batch:
                        collection.render_detail(dataset)
                    if batch:
                        collection.update_listings(batch)
                    if len(batch) < batchsize:
                        break
        log.info('Initialized from %s', self.config.filename)

    def cleanup_discarded(self):
        collections = self.collections
        with scoped_session(self) as session:
            query = session.query(Dataset.collection, Dataset.id)\
                           .filter(Dataset.discarded.is_(True))\
                           .order_by(Dataset.collection)
            datasets = [(col, [x[1] for x in ids])
                        for col, ids in groupby(query, lambda x: x[0])]
            if not datasets:
                return

            for col, ids in datasets:
                collection = collections[col]
                model = collection.model
                listing = model.Listing.__table__
                for secondary in model.secondaries.values():
                    stmt = secondary.delete()\
                                    .where(secondary.c.listing_id.in_(ids))
                    session.execute(stmt)

                stmt = listing.delete()\
                              .where(listing.c.id.in_(ids))
                session.execute(stmt)

                stmt = (dataset_tag.delete()  # pylint: disable=no-value-for-parameter
                        .where(dataset_tag.c.dataset_id.in_(ids)))
                session.execute(stmt)

                session.query(Comment)\
                       .filter(Comment.dataset_id.in_(ids))\
                       .delete(synchronize_session=False)

                session.query(File)\
                       .filter(File.dataset_id.in_(ids))\
                       .delete(synchronize_session=False)

                session.query(Dataset)\
                       .filter(Dataset.id.in_(ids))\
                       .delete(synchronize_session=False)

            # TODO: Cleanup corresponding store paths

    def cleanup_relations(self):
        """Cleanup listing relations."""
        collections = self.collections
        with scoped_session(self) as session:
            for relation in [x for col in collections.values()
                             for x in col.model.relations.values()]:
                session.query(relation)\
                       .filter(~relation.listing.any())\
                       .delete(synchronize_session=False)

    def cleanup_tags(self):
        with scoped_session(self) as session:
            session.query(Tag)\
                      .filter(~Tag.datasets.any())\
                      .delete(synchronize_session=False)

    def restore_database(self, datasets=None, users=None):
        for user in users or []:
            user.setdefault('realm', 'marv')
            user.setdefault('realmuid', '')
            groups = user.pop('groups', [])
            self.user_add(_restore=True, **user)
            for grp in groups:
                try:
                    self.group_adduser(grp, user['name'])
                except ValueError:
                    self.group_add(grp)
                    self.group_adduser(grp, user['name'])

        for key, sets in (datasets or {}).items():
            key = self.collections.keys()[0] if key == 'DEFAULT_COLLECTION' else key
            self.collections[key].restore_datasets(sets)

    def listtags(self, collections=None):
        with scoped_session(self) as session:
            query = session.query(Tag.value)
            if collections:
                query = query.filter(Tag.collection.in_(collections))
            query = query.group_by(Tag.value)\
                         .order_by(Tag.value)
        tags = [x[0] for x in query]
        return tags

    def query(self, collections=None, discarded=None, outdated=None, path=None, tags=None,
              abbrev=None, missing=None):
        # pylint: disable=too-many-arguments

        abbrev = 10 if abbrev is True else abbrev
        discarded = bool(discarded)
        with scoped_session(self) as session:
            query = session.query(Dataset.setid)

            if collections:
                query = query.filter(Dataset.collection.in_(collections))

            if outdated:
                query = query.filter(Dataset.status.op('&')(STATUS_OUTDATED) == STATUS_OUTDATED)

            query = query.filter(Dataset.discarded.is_(discarded))

            if path:
                relquery = session.query(File.dataset_id)\
                                     .filter(File.path.like(f'{esc(path)}%', escape='$'))\
                                     .group_by(File.dataset_id)
                query = query.filter(Dataset.id.in_(relquery.subquery()))

            if missing:
                relquery = session.query(File.dataset_id)\
                                     .filter(File.missing.is_(True))\
                                     .group_by(File.dataset_id)
                query = query.filter(Dataset.id.in_(relquery.subquery()))

            if tags:
                relquery = session.query(dataset_tag.c.dataset_id)\
                                     .join(Tag)\
                                     .filter(Tag.value.in_(tags))
                query = query.filter(Dataset.id.in_(relquery.subquery()))

            setids = [x[0][:abbrev] if abbrev else x[0]
                      for x in query.order_by(Dataset.setid)]
        return setids

    def run(self, setid, selected_nodes=None, deps=None, force=None, keep=None,
            force_dependent=None, update_detail=None, update_listing=None,
            excluded_nodes=None, cachesize=None):
        # pylint: disable=too-many-arguments,too-many-locals

        assert not force_dependent or selected_nodes

        excluded_nodes = set(excluded_nodes or [])
        with scoped_session(self) as session:
            dataset = session.query(Dataset).filter(Dataset.setid == str(setid))\
                             .options(joinedload(Dataset.files))\
                             .one()
            collection = self.collections[dataset.collection]
            selected_nodes = set(selected_nodes or [])
            if not (selected_nodes or update_listing or update_detail):
                selected_nodes.update(collection.listing_deps)
                selected_nodes.update(collection.detail_deps)
            persistent = collection.nodes
            try:
                nodes = {persistent[name] if ':' not in name else utils.find_obj(name)
                         for name in selected_nodes
                         if name not in excluded_nodes
                         if name != 'dataset'}
            except KeyError as e:
                raise UnknownNode(dataset.collection, e.args[0])

            if force_dependent:
                nodes.update(x for name in selected_nodes
                             for x in persistent[name].dependent)
            nodes = sorted(nodes)

            storedir = self.config.marv.storedir
            store = Store(storedir, persistent)

            changed = False
            try:
                if nodes:
                    changed = run_nodes(dataset, nodes, store, force=force,
                                        persistent=persistent,
                                        deps=deps, cachesize=cachesize)
            finally:
                if not keep:
                    for tmpdir, tmpdir_fd in store.pending.values():
                        store.logdebug('Cleaning up %r', tmpdir)
                        shutil.rmtree(tmpdir)
                        fcntl.flock(tmpdir_fd, fcntl.LOCK_UN)
                        os.close(tmpdir_fd)
                    store.pending.clear()

            if changed or update_detail:
                collection.render_detail(dataset)
                log.verbose('%s detail rendered', setid)
            if changed or update_listing:
                collection.update_listings([dataset])
                log.verbose('%s listing rendered', setid)

        return changed

    def scan(self, dry_run=None):
        for collection in self.collections.values():
            for scanroot in collection.scanroots:
                collection.scan(scanroot, dry_run)

    def comment(self, username, message, ids):
        now = int(utils.now() * 1000)
        comments = [Comment(dataset_id=id, author=username, time_added=now,
                            text=message)
                    for id in ids]
        with scoped_session(self) as session:
            session.add_all(comments)

    def tag(self, setids, add=None, remove=None):
        assert setids
        assert add or remove, (add, remove)
        add = sorted(add or [])
        remove = remove or []
        addremove = set(add) | set(remove)
        assert len(addremove) == len(add) + len(remove), (add, remove)

        with scoped_session(self) as session:
            # pylint: disable=no-member
            query = session.query(Dataset.collection, Dataset.id, Dataset.setid)\
                           .filter(Dataset.setid.in_(setids))\
                           .order_by(Dataset.collection)
            # pylint: enable=no-member
            for collection, group in groupby(query, key=lambda x: x[0]):
                setidmap = {setid: id for _, id, setid in group}
                dataset_ids = setidmap.values()

                if add:
                    stmt = Tag.__table__.insert().prefix_with('OR IGNORE')
                    session.execute(stmt, [{'collection': collection,
                                            'value': x} for x in add])

                tags = {value: id for id, value in (
                    session.query(Tag.id, Tag.value)
                    .filter(Tag.collection == collection)
                    .filter(Tag.value.in_(addremove)))}

                if add:
                    stmt = dataset_tag.insert().prefix_with('OR IGNORE')  # pylint: disable=no-value-for-parameter
                    session.execute(stmt,
                                    [{'dataset_id': x, 'tag_id': y} for x, y in
                                     product(dataset_ids, (tags[x] for x in add))])

                if remove:
                    where = (dataset_tag.c.tag_id.in_(tags[x] for x in remove)
                             & dataset_tag.c.dataset_id.in_(dataset_ids))
                    stmt = dataset_tag.delete().where(where)  # pylint: disable=no-value-for-parameter
                    session.execute(stmt)

    def authenticate(self, username, password):
        if not username or not password:
            return False
        with scoped_session(self) as session:
            try:
                user = session.query(User).filter_by(name=username, realm='marv').one()
            except NoResultFound:
                return False
            hashed = user.password.encode('utf-8')
        return bcrypt.hashpw(password, hashed) == hashed

    def user_add(self, name, password, realm, realmuid, given_name=None, family_name=None,
                 email=None, time_created=None, time_updated=None, _restore=None):
        # pylint: disable=too-many-arguments
        try:
            if not _restore:
                password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            now = int(utils.now())
            if not time_created:
                time_created = now
            if not time_updated:
                time_updated = now
            user = User(name=name, password=password, realm=realm, given_name=given_name,
                        family_name=family_name, email=email, realmuid=realmuid,
                        time_created=time_created, time_updated=time_updated)
            with scoped_session(self) as session:
                session.add(user)
        except IntegrityError:
            raise ValueError(f'User {name} exists already')

    def user_rm(self, username):
        try:
            with scoped_session(self) as session:
                user = session.query(User).filter_by(name=username).one()
                session.delete(user)
        except NoResultFound:
            raise ValueError(f'User {username} does not exist')

    def user_pw(self, username, password):
        with scoped_session(self) as session:
            try:
                user = session.query(User).filter_by(name=username).one()
            except NoResultFound:
                raise ValueError(f'User {username} does not exist')

            user.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            user.time_updated = int(utils.now())

    def group_add(self, groupname):
        try:
            with scoped_session(self) as session:
                group = Group(name=groupname)
                session.add(group)
        except IntegrityError:
            raise ValueError(f'Group {groupname} exists already')

    def group_rm(self, groupname):
        try:
            with scoped_session(self) as session:
                group = session.query(Group).filter_by(name=groupname).one()
                session.delete(group)
        except NoResultFound:
            raise ValueError(f'Group {groupname} does not exist')

    def group_adduser(self, groupname, username):
        with scoped_session(self) as session:
            try:
                group = session.query(Group).filter_by(name=groupname).one()
            except NoResultFound:
                raise ValueError(f'Group {groupname} does not exist')
            try:
                user = session.query(User).filter_by(name=username).one()
            except NoResultFound:
                raise ValueError(f'User {username} does not exist')
            group.users.append(user)

    def group_rmuser(self, groupname, username):
        with scoped_session(self) as session:
            try:
                group = session.query(Group).filter_by(name=groupname).one()
            except NoResultFound:
                raise ValueError(f'Group {groupname} does not exist')
            try:
                user = session.query(User).filter_by(name=username).one()
            except NoResultFound:
                raise ValueError(f'User {username} does not exist')
            if user in group.users:
                group.users.remove(user)


def dump_database(dburi):  # noqa: C901
    """Dump database.

    The structure of the database is reflected and therefore also
    older databases, not matching the current version of marv, can be
    dumped.
    """
    # pylint: disable=too-many-locals,too-many-statements

    engine = sqla.create_engine(dburi)
    meta = sqla.MetaData(engine)
    meta.reflect()
    con = engine.connect()
    tables = {
        k: v for k, v in meta.tables.items()
        if not k.startswith('listing_')
        if not k.startswith('sqlite_')
    }
    select = sqla.sql.select

    def rows2dcts(stmt):
        result = con.execute(stmt)
        keys = result.keys()
        return [dict(zip(keys, row)) for row in result]

    comments = {}
    comment_t = tables.pop('comment')
    stmt = select([comment_t]).order_by(comment_t.c.dataset_id, comment_t.c.id)
    for did, grp in groupby(rows2dcts(stmt), key=lambda x: x['dataset_id']):
        assert did not in comments
        comments[did] = lst = []
        for comment in grp:
            # Everything except these fields is included in the dump
            del comment['dataset_id']
            del comment['id']
            lst.append(comment)

    files = {}
    file_t = tables.pop('file')
    stmt = select([file_t]).order_by(file_t.c.dataset_id, file_t.c.idx)
    for did, grp in groupby(rows2dcts(stmt), key=lambda x: x['dataset_id']):
        assert did not in files
        files[did] = lst = []
        for file in grp:
            # Everything except these fields is included in the dump
            del file['dataset_id']
            del file['idx']
            lst.append(file)

    tags = {}
    dataset_tag_t = tables.pop('dataset_tag')
    tag_t = tables.pop('tag')
    stmt = select([dataset_tag_t, tag_t]).where(dataset_tag_t.c.tag_id == tag_t.c.id)\
                                         .order_by(dataset_tag_t.c.dataset_id, tag_t.c.value)
    for did, grp in groupby(rows2dcts(stmt), key=lambda x: x['dataset_id']):
        assert did not in tags
        tags[did] = lst = []
        for tag in grp:
            del tag['dataset_id']
            del tag['collection']
            del tag['id']
            del tag['tag_id']
            lst.append(tag.pop('value'))
            assert not tag

    dump = {}
    dump['datasets'] = collections = {}
    dataset_t = tables.pop('dataset')
    stmt = select([dataset_t]).order_by(dataset_t.c.setid)
    for dataset in rows2dcts(stmt):
        did = dataset.pop('id')  # Everything except this is included in the dump
        dataset['comments'] = comments.pop(did, [])
        dataset['files'] = files.pop(did)
        dataset['tags'] = tags.pop(did, [])
        collections.setdefault(dataset.pop('collection'), []).append(dataset)

    assert not comments, comments
    assert not files, files
    assert not tags, tags

    groups = {}
    group_t = tables.pop('group')
    user_group_t = tables.pop('user_group')
    stmt = select([user_group_t, group_t]).where(user_group_t.c.group_id == group_t.c.id)\
                                          .order_by(user_group_t.c.user_id, group_t.c.name)
    for uid, grp in groupby(rows2dcts(stmt), key=lambda x: x['user_id']):
        assert uid not in groups
        groups[uid] = lst = []
        for group in grp:
            del group['user_id']
            del group['group_id']
            del group['id']
            name = group.pop('name')
            assert not group
            lst.append(name)

    dump['users'] = users = []
    user_t = tables.pop('user')
    stmt = select([user_t]).order_by(user_t.c.name)
    for user in rows2dcts(select([user_t])):
        user_id = user.pop('id')  # Everything except this is included in the dump
        user['groups'] = groups.pop(user_id, [])
        users.append(user)

    assert not groups, groups
    assert not tables, tables.keys()

    return dump
