# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import fcntl
import os
import shutil
import sys
from itertools import count, product
from logging import getLogger
from pathlib import Path
from uuid import uuid4

import tortoise
from pkg_resources import resource_filename

from marv_node.run import run_nodes
from marv_store import Store
from . import utils
from .collection import Collections
from .config import Config
from .db import Database, scoped_session
from .model import Dataset, Group


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
    sitedir = Path(siteconf).parent
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
            'venv': str(sitedir / 'venv'),
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
    def __init__(self, siteconf):
        self.config = make_config(siteconf)
        # TODO: maybe ordereddict for meta, or generate multiple keys
        self.config.marv.oauth = {
            line.split(' ', 1)[0]: [field.strip() for field in line.split('|')]
            for line in self.config.marv.oauth
        }
        self.collections = Collections(config=self.config, site=self)
        self.db = Database()  # pylint: disable=invalid-name

    @classmethod
    async def create(cls, siteconf, init=None):
        site = cls(siteconf)
        sys.path.append(f'{site.config.marv.venv}/lib/python3.7/site-packages')

        if init:
            site.init_directory()

        # Generate all dynamic models
        from . import model
        model.__models__ += (y for x in site.collections.values() for y in x.model)

        assert site.config.marv.dburi.startswith('sqlite://')
        await tortoise.Tortoise.init(config={
            'connections': {
                'default': {
                    'engine': 'tortoise.backends.sqlite',
                    'credentials': {
                        'file_path': site.config.marv.dburi[9:],
                        'foreign_keys': 1,
                    },
                },
            },
            'apps': {
                'models': {
                    'models': ['marv.model'],
                },
            },
        })

        await site.db.initialize_connections()

        try:
            if init:
                await site.init_database()

            async with scoped_session(site.db) as transaction:
                try:
                    await transaction.execute_query(
                        'SELECT name FROM sqlite_master WHERE type="table"',
                    )
                except ValueError:
                    raise DBNotInitialized()
        except BaseException:
            await site.destroy()
            raise

        return site

    async def destroy(self):
        await self.db.close_connections()
        await tortoise.Tortoise.close_connections()

    def load_for_web(self):
        _ = [getattr(x, y) and None for x, y, in product(
            self.collections.values(),
            ('compare', 'filter_specs', 'listing_columns', 'model',
             'sortcolumn', 'sortorder', 'summary_items'))]

    def init_directory(self):
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
            dbdir = os.path.dirname(self.config.marv.dburi.replace('sqlite://', ''))
            os.mkdir(dbdir)
            log.verbose('Created %s', dbdir)
        except OSError as e:
            if e.errno != 17:
                raise

    async def init_database(self):
        async with scoped_session(self.db) as transaction:
            prefixes = [f'l_{col}' for col in self.collections.keys()]
            tables = {
                name for name in [
                    x['name'] for x in await transaction.execute_query(
                        'SELECT name FROM sqlite_master WHERE type="table"',
                    )
                ]
                if any(name.startswith(prefix) for prefix in prefixes)
            }
            for table in sorted(tables, key=len, reverse=True):
                await transaction.execute_query(f'DROP TABLE {table};')

        await tortoise.Tortoise.generate_schemas()

        async with scoped_session(self.db) as transaction:
            for name in ('admin', ):
                if not await Group.filter(name=name).using_db(transaction).count():
                    await Group.create(name=name, using_db=transaction)

            log.verbose('Initialized database %s', self.config.marv.dburi)
            for col, collection in self.collections.items():
                loop = count()
                batchsize = 50
                # TODO: increase verbosity and probably introduce --reinit
                while True:
                    batch = await Dataset.filter(collection=col)\
                                         .using_db(transaction)\
                                         .prefetch_related('files')\
                                         .limit(batchsize)\
                                         .offset(batchsize*next(loop))\
                                         .all()
                    for dataset in batch:
                        collection.render_detail(dataset)
                    if batch:
                        await collection.update_listings(batch, transaction=transaction)
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
        await self.db.cleanup_listing_relations(descs)

    async def restore_database(self, datasets=None, users=None):
        for user in users or []:
            user.setdefault('realm', 'marv')
            user.setdefault('realmuid', '')
            groups = user.pop('groups', [])
            await self.db.user_add(_restore=True, **user)
            for grp in groups:
                try:
                    await self.db.group_adduser(grp, user['name'])
                except ValueError:
                    await self.db.group_add(grp)
                    await self.db.group_adduser(grp, user['name'])

        for key, sets in (datasets or {}).items():
            key = self.collections.keys()[0] if key == 'DEFAULT_COLLECTION' else key
            await self.collections[key].restore_datasets(sets)

    async def run(self, setid, selected_nodes=None, deps=None, force=None, keep=None,
                  force_dependent=None, update_detail=None, update_listing=None,
                  excluded_nodes=None, cachesize=None):
        # pylint: disable=too-many-arguments,too-many-locals

        assert not force_dependent or selected_nodes

        excluded_nodes = set(excluded_nodes or [])
        dataset = (await self.db.get_datasets_by_setids([setid], prefetch=['files']))[0]
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
            nodes.update(x for name in selected_nodes for x in persistent[name].dependent)
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
            await collection.update_listings([dataset])
            log.verbose('%s listing rendered', setid)

        return changed

    async def scan(self, dry_run=None):
        for collection in self.collections.values():
            for scanroot in collection.scanroots:
                await collection.scan(scanroot, dry_run)
