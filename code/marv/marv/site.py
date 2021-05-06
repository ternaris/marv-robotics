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

from pypika import SQLLiteQuery as Query
from pypika import Table

from marv.utils import within_pyinstaller_bundle
from marv_api.utils import find_obj
from marv_node.node import Node
from marv_node.run import run_nodes
from marv_store import Store

from .collection import Collections
from .config import Config, ConfigError
from .db import Database, DBNotInitialized, Tortoise, create_or_ignore, scoped_session
from .model import Dataset, Group, User

log = getLogger(__name__)


class SiteError(Exception):
    pass


def make_config(siteconf):
    return Config.from_file(siteconf)


def load_sitepackages(sitepackages):
    import site  # pylint: disable=import-outside-toplevel
    site.USER_SITE = sitepackages
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
        self.collections = Collections(config=self.config, site=self)
        self.db = self.Database([y for x in self.collections.values() for y in x.model],  # pylint: disable=invalid-name
                                self.config)

    @classmethod
    async def create(cls, siteconf, init=None):  # noqa: C901
        site = cls(siteconf)
        if within_pyinstaller_bundle():
            load_sitepackages(site.config.marv.sitepackages)
        site.config.marv.resourcedir.mkdir(exist_ok=True)

        site.db.check_db_version(site.config.marv.dburi, missing_ok=init)

        dbpath = Path(site.config.marv.dburi.split('sqlite://', 1)[1])
        store_db_version = not dbpath.exists()

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
        models = site.db.MODELS + site.db.listing_models

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
                await site.init_database(store_db_version=store_db_version)

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

    async def init_database(self, store_db_version=False):
        async with scoped_session(self.db) as txn:
            await self.drop_listings(txn)

        await Tortoise.generate_schemas()

        async with scoped_session(self.db) as txn:
            for name in ('marv:user:anonymous', 'marv:users', 'admin'):
                await Group.get_or_create(name=name, using_db=txn)

            for name in ('marv:anonymous',):
                user = await User.get_or_create(name=name, realm='marv', realmuid='',
                                                active=True, using_db=txn)
                await user[0].groups.add(
                    await Group.get(name=name.replace(':', ':user:')).using_db(txn),
                    using_db=txn,
                )

            if store_db_version:
                await self.store_db_version(txn)

            await create_or_ignore('acn', id=1, txn=txn)
            await create_or_ignore('acn', id=2, txn=txn)
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
            nodes = {persistent[name] if ':' not in name else Node.from_dag_node(find_obj(name))
                     for name in selected_nodes
                     if name not in excluded_nodes
                     if name != 'dataset'}
        except KeyError as exc:
            raise ConfigError(f'Collection {collection.name!r} has no node {exc}')

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
                                          deps=deps, cachesize=cachesize, site=self)
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
