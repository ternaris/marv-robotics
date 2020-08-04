# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import fcntl
import os
import shutil
import sqlite3
import sys
import sysconfig
from itertools import count, product
from logging import getLogger
from pathlib import Path
from uuid import uuid4

from pkg_resources import resource_filename
from pypika import SQLLiteQuery as Query, Table

from marv_node.run import run_nodes
from marv_store import Store
from . import utils
from .collection import Collections
from .config import Config
from .db import DBNotInitialized, DBVersionError
from .db import Database, Tortoise, create_or_ignore, scoped_session
from .model import Dataset, Group, User


DEFAULT_NODES = """
marv_nodes:dataset
marv_nodes:meta_table
marv_nodes:summary_keyval
"""

DEFAULT_FILTERS = """
name       | Name       | substring         | string   | (get "dataset.name")
setid      | Set Id     | startswith        | string   | (get "dataset.id")
size       | Size       | lt le eq ne ge gt | filesize | (sum (get "dataset.files[:].size"))
status     | Status     | any all           | subset   | (status)
tags       | Tags       | any all           | subset   | (tags)
comments   | Comments   | substring         | string   | (comments)
files      | File paths | substring_any     | string[] | (get "dataset.files[:].path")
time_added | Added      | lt le eq ne ge gt | datetime | (get "dataset.time_added")
"""

DEFAULT_LISTING_COLUMNS = """
name       | Name   | route    | (detail_route (get "dataset.id") (get "dataset.name"))
size       | Size   | filesize | (sum (get "dataset.files[:].size"))
status     | Status | icon[]   | (status)
tags       | Tags   | pill[]   | (tags)
time_added | Added  | datetime | (get "dataset.time_added")
"""

DEFAULT_LISTING_SUMMARY = """
datasets | datasets | int       | (len (rows))
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
    sitedir = Path(siteconf).parent
    py_ver = sysconfig.get_python_version()
    defaults = {
        'marv': {
            'acl': 'marv_webapi.acls:authenticated',
            'dburi': 'sqlite://' + str(sitedir / 'db' / 'db.sqlite'),
            'frontenddir': str(sitedir / 'frontend'),
            'oauth': '',
            'reverse_proxy': None,
            'sessionkey_file': str(sitedir / 'sessionkey'),
            'staticdir': str(sitedir / resource_filename('marv_ludwig', 'static')),
            'storedir': str(sitedir / 'store'),
            'upload_checkpoint_commands': '',
            'venv': str(sitedir / 'venv'),
            'sitepackages': str(sitedir / 'venv' / 'lib' / f'python{py_ver}' / 'site-packages'),
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
            'upload_checkpoint_commands': 'cmd_lines',
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


def load_sitepackages(sitepackages):
    import site  # pylint: disable=import-outside-toplevel
    site.USER_SITE = sitepackages
    sitepackages = Path(sitepackages)
    sitepackages.mkdir(parents=True, exist_ok=True)
    if str(sitepackages) not in sys.path:
        sys.path.append(str(sitepackages))
    try:
        with (sitepackages / 'easy-install.pth').open('r') as f:
            for directory in f.readlines():
                if directory[0] == '#' or directory.startswith('import'):
                    continue
                directory = directory.strip()
                if directory not in sys.path:
                    sys.path.append(directory)
    except FileNotFoundError:
        pass


class Site:
    Database = Database

    def __init__(self, siteconf):
        self.config = make_config(siteconf)
        # TODO: maybe ordereddict for meta, or generate multiple keys
        self.config.marv.oauth = {
            line.split(' ', 1)[0]: [field.strip() for field in line.split('|')]
            for line in self.config.marv.oauth
        }
        self.collections = Collections(config=self.config, site=self)
        self.db = self.Database()  # pylint: disable=invalid-name
        self.createdb = True

    @classmethod
    async def create(cls, siteconf, init=None):  # noqa: C901
        site = cls(siteconf)
        if utils.within_pyinstaller_bundle():
            load_sitepackages(site.config.marv.sitepackages)

        assert site.config.marv.dburi.startswith('sqlite://')
        dbpath = Path(site.config.marv.dburi.split('://', 1)[1])
        site.createdb = not dbpath.exists()
        if not site.createdb:
            site.check_db_version()
        elif not init:
            raise DBNotInitialized('There is no marv database.')

        if init:
            site.init_directory()

        try:
            fd = os.open(site.config.marv.sessionkey_file,
                         os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except OSError as e:
            if e.errno != 17:
                raise
        else:
            with os.fdopen(fd, 'w') as f:
                f.write(str(uuid4()))
            log.verbose('Generated %s', site.config.marv.sessionkey_file)

        # Generate all dynamic models
        models = site.db.MODELS + [y for x in site.collections.values() for y in x.model]

        await Tortoise.init(config={
            'connections': {
                'default': {
                    'engine': 'tortoise.backends.sqlite',
                    'credentials': {
                        'file_path': dbpath,
                        'foreign_keys': 1,
                    },
                },
            },
            'apps': {
                'models': {
                    'models': models,
                },
            },
        })

        await site.db.initialize_connections()

        try:
            if init:
                await site.init_database()

            async with scoped_session(site.db) as txn:
                try:
                    await txn.execute_query('SELECT name FROM sqlite_master WHERE type="table"')
                except ValueError:
                    raise DBNotInitialized
        except BaseException:
            await site.destroy()
            raise

        return site

    async def destroy(self):
        await self.db.close_connections()
        await Tortoise.close_connections()

    def load_for_web(self):
        _ = [getattr(x, y) and None for x, y, in product(
            self.collections.values(),
            ('compare', 'filter_specs', 'listing_columns', 'model',
             'sortcolumn', 'sortorder', 'summary_items'))]

    def init_directory(self):
        try:
            os.mkdir(self.config.marv.storedir)
            log.verbose('Created %s', self.config.marv.storedir)
        except OSError as e:
            if e.errno != 17:
                raise

        try:
            dbdir = os.path.dirname(self.config.marv.dburi.replace('sqlite://', ''))
            os.mkdir(dbdir)
            log.verbose('Created %s', dbdir)
        except OSError as e:
            if e.errno != 17:
                raise

    def check_db_version(self):
        dbpath = Path(self.config.marv.dburi.split('://', 1)[1])
        metadata = Table('metadata')
        required = self.db.VERSION
        try:
            conn = sqlite3.connect(f'file:{dbpath}?mode=ro', uri=True)
            with conn:
                have = conn.execute(Query.from_(metadata)
                                    .select(metadata.value)
                                    .where(metadata.key == 'database_version')
                                    .get_sql())\
                           .fetchone()[0]
                if have != required:
                    raise DBVersionError(
                        f'DB version on disk "{have}", but "{required}" required.',
                    )
        except (sqlite3.OperationalError, TypeError):
            raise DBVersionError(
                'DB version is unknown, metadata table or version entry missing.',
            )
        finally:
            conn.close()

    async def store_db_version(self, txn):
        metadata = Table('metadata')
        await txn.exq(Query.into(metadata)
                      .columns(metadata.key, metadata.value)
                      .insert('database_version', self.db.VERSION))

    async def drop_listings(self, txn):
        prefixes = [f'l_{col}' for col in self.collections.keys()]
        tables = {
            name for name in [
                x['name'] for x in (await txn.execute_query(
                    'SELECT name FROM sqlite_master WHERE type="table"',
                ))[1]
            ]
            if any(name.startswith(prefix) for prefix in prefixes)
        }
        for table in sorted(tables, key=len, reverse=True):
            await txn.execute_query(f'DROP TABLE {table};')

    async def init_database(self):
        async with scoped_session(self.db) as txn:
            await self.drop_listings(txn)

        await Tortoise.generate_schemas()

        async with scoped_session(self.db) as txn:
            for name in ('marv:user:anonymous', 'marv:users', 'admin'):
                await Group.get_or_create(name=name, using_db=txn)

            for name in ('marv:anonymous',):
                user = await User.get_or_create(name=name, realm='marv', realmuid='',
                                                using_db=txn)
                await user[0].groups.add(
                    await Group.get(name=name.replace(':', ':user:')).using_db(txn),
                    using_db=txn,
                )

            if self.createdb:
                await self.store_db_version(txn)

            await create_or_ignore('acn', id=1, txn=txn)
            for name in self.collections:
                await create_or_ignore('collection', name=name, acn_id=1, txn=txn)

            log.verbose('Initialized database %s', self.config.marv.dburi)
            for col, collection in self.collections.items():
                loop = count()
                batchsize = 50
                # TODO: increase verbosity and probably introduce --reinit
                while True:
                    batch = await Dataset.filter(collection__name=col)\
                                         .using_db(txn)\
                                         .prefetch_related('files')\
                                         .limit(batchsize)\
                                         .offset(batchsize*next(loop))\
                                         .all()
                    for dataset in batch:
                        collection.render_detail(dataset)
                    if batch:
                        await collection.update_listings(batch, txn=txn)
                    if len(batch) < batchsize:
                        break
        log.info('Initialized from %s', self.config.filename)

    async def cleanup_discarded(self):
        descs = {
            key: x.table_descriptors
            for key, x in self.collections.items()
        }
        await self.db.cleanup_discarded(descs)
        # TODO: Cleanup corresponding store paths

    async def cleanup_relations(self):
        descs = {key: x.table_descriptors for key, x in self.collections.items()}
        await self.db.delete_listing_rel_values_without_ref(descs)

    async def restore_database(self, **kw):
        await self.db.restore_database(self, kw)

    async def run(self, setid, selected_nodes=None, deps=None, force=None, keep=None,
                  force_dependent=None, update_detail=None, update_listing=None,
                  excluded_nodes=None, cachesize=None):
        # pylint: disable=too-many-arguments,too-many-locals,too-many-branches

        assert not force_dependent or selected_nodes

        excluded_nodes = set(excluded_nodes or [])
        async with scoped_session(self.db) as txn:
            dataset = await Dataset.get(setid=setid)\
                                   .prefetch_related('collection', 'files')\
                                   .using_db(txn)
        collection = self.collections[dataset.collection.name]
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
            nodes.update(x for name in selected_nodes for x in persistent[name].dependent)
        nodes = sorted(nodes)

        storedir = self.config.marv.storedir
        store = Store(storedir, persistent)

        changed = False
        try:
            if nodes:
                changed = await run_nodes(dataset, nodes, store, force=force,
                                          persistent=persistent,
                                          deps=deps, cachesize=cachesize)
        finally:
            if not keep:
                for stream in store.pending:
                    if stream.streamfile:
                        stream.streamfile.close()
                for stream in store.readstreams:
                    if stream.streamfile:
                        stream.streamfile.close()
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
            await collection.update_listings([dataset])
            log.verbose('%s listing rendered', setid)

        return changed

    async def scan(self, dry_run=None):
        for collection in self.collections.values():
            for scanroot in collection.scanroots:
                await collection.scan(scanroot, dry_run)
