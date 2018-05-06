# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import json
import os
import shutil
import time
from itertools import count, groupby, product
from logging import getLogger
from uuid import uuid4

from flask import current_app as app
from pkg_resources import resource_filename

from marv_node.run import run_nodes
from marv_store import Store
from .collection import esc
from .collection import Collections
from .config import Config
from .model import STATUS_MISSING, STATUS_OUTDATED
from .model import Comment, Dataset, File, Group, Tag, User, dataset_tag, db
from .utils import find_obj


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
        }
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


class Site(object):
    def __init__(self, siteconf):
        self.config = make_config(siteconf)
        # TODO: maybe ordereddict for meta, or generate multiple keys
        self.config.marv.oauth = dict(
            (i.split(' ')[0], [s.strip() for s in i.split('|')]
        ) for i in self.config.marv.oauth)
        self.collections = Collections(config=self.config)

    def load_for_web(self):
        _ = [getattr(x, y) and None for x, y, in product(
            self.collections.values(),
            ('compare', 'filter_specs', 'listing_columns', 'model',
             'sortcolumn', 'sortorder', 'summary_items'))]

    def init(self):
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
        except OSError:
            if e.errno != 17:
                raise

        # TODO: maybe this should be an explicit method...
        # load models
        _ = [x.model for x in self.collections.values()]

        prefixes = ['listing_{}'.format(col) for col in self.collections.keys()]
        result = db.session.execute('SELECT name FROM sqlite_master WHERE type="table";')
        tables = {name for name in [x[0] for x in result]
                  if any(name.startswith(prefix) for prefix in prefixes)}
        for table in [x for x in tables if x.endswith('_sec')]:
            db.session.execute('DROP TABLE {};'.format(table))
            tables.discard(table)
        for table in [x for x in tables if x not in prefixes]:
            db.session.execute('DROP TABLE {};'.format(table))
            tables.discard(table)
        for table in tables:
            db.session.execute('DROP TABLE {};'.format(table))

        db.create_all()
        for name in ('admin', ):
            if not Group.query.filter(Group.name==name).count():
                db.session.add(Group(name=name))
                db.session.commit()

        try:
            with open('users', 'r') as usersfile:
                users = json.load(usersfile)
                for name, password in users.items():
                    if not User.query.filter(User.name==name).count():
                        db.session.add(User(name=name, password=password))
                        db.session.commit()
            os.rename('users', 'users.imported')
        except IOError:
            pass

        log.verbose('Initialized database %s', app.config['SQLALCHEMY_DATABASE_URI'])
        for col in self.collections.keys():
            collection = self.collections[col]
            loop = count()
            batchsize = 50
            # TODO: increase verbosity and probably introduce --reinit
            while True:
                batch = db.session.query(Dataset)\
                                  .filter(Dataset.collection == col)\
                                  .options(db.joinedload(Dataset.files))\
                                  .limit(batchsize)\
                                  .offset(batchsize*loop.next())\
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
        query = db.session.query(Dataset.collection, Dataset.id)\
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
                db.session.execute(stmt)

            stmt = listing.delete()\
                          .where(listing.c.id.in_(ids))
            db.session.execute(stmt)

            stmt = dataset_tag.delete()\
                              .where(dataset_tag.c.dataset_id.in_(ids))
            db.session.execute(stmt)

            db.session.query(Comment)\
                      .filter(Comment.dataset_id.in_(ids))\
                      .delete(synchronize_session=False)

            db.session.query(File)\
                      .filter(File.dataset_id.in_(ids))\
                      .delete(synchronize_session=False)

            db.session.query(Dataset)\
                      .filter(Dataset.id.in_(ids))\
                      .delete(synchronize_session=False)

        db.session.commit()
        # TODO: Cleanup corresponding store paths

    def cleanup_relations(self):
        """Cleanup listing relations"""
        collections = self.collections
        for relation in [x for col in collections.values()
                         for x in col.model.relations.values()]:
            db.session.query(relation)\
                       .filter(~relation.listing.any())\
                       .delete(synchronize_session=False)
        db.session.commit()

    def cleanup_tags(self):
        db.session.query(Tag)\
                  .filter(~Tag.datasets.any())\
                  .delete(synchronize_session=False)
        db.session.commit()

    def restore_database(self, datasets=None, users=None):
        for user in users or []:
            user.setdefault('realm', 'marv')
            user.setdefault('realmuid', '')
            app.um.user_add(**user)

        for key, sets in (datasets or {}).items():
            key = self.collections.keys()[0] if key == 'DEFAULT_COLLECTION' else key
            self.collections[key].restore_datasets(sets)

    def listtags(self, collections=None):
        query = db.session.query(Tag.value)
        if collections:
            query = query.filter(Tag.collection.in_(collections))
        query = query.group_by(Tag.value)\
                     .order_by(Tag.value)
        tags = [x[0] for x in query]
        return tags

    def query(self, collections=None, discarded=None, outdated=None,
              path=None, tags=None, abbrev=None):
        abbrev = 10 if abbrev is True else abbrev
        discarded = bool(discarded)
        query = db.session.query(Dataset.setid)

        if collections:
            query = query.filter(Dataset.collection.in_(collections))

        if outdated:
            query = query.filter(Dataset.status.op('&')(STATUS_OUTDATED) == STATUS_OUTDATED)

        query = query.filter(Dataset.discarded.is_(discarded))

        if path:
            relquery = db.session.query(File.dataset_id)\
                                 .filter(File.path.like('{}%'.format(esc(path)), escape='$'))\
                                 .group_by(File.dataset_id)
            query = query.filter(Dataset.id.in_(relquery.subquery()))

        if tags:
            relquery = db.session.query(dataset_tag.c.dataset_id)\
                                 .join(Tag)\
                                 .filter(Tag.value.in_(tags))
            query = query.filter(Dataset.id.in_(relquery.subquery()))

        setids = [x[0][:abbrev] if abbrev else x[0]
                  for x in query.order_by(Dataset.setid)]
        return setids

    def run(self, setid, selected_nodes=None, deps=None, force=None, keep=None,
            force_dependent=None, update_detail=None, update_listing=None,
            excluded_nodes=None, cachesize=None):
        assert not force_dependent or selected_nodes

        excluded_nodes = set(excluded_nodes or [])
        dataset = Dataset.query.filter(Dataset.setid == str(setid))\
                               .options(db.joinedload(Dataset.files))\
                               .one()
        collection = self.collections[dataset.collection]
        selected_nodes = set(selected_nodes or [])
        if not (selected_nodes or update_listing or update_detail):
            selected_nodes.update(collection.listing_deps)
            selected_nodes.update(collection.detail_deps)
        persistent = collection.nodes
        try:
            nodes = {persistent[name] if not ':' in name else find_obj(name)
                     for name in selected_nodes
                     if name not in excluded_nodes
                     if name != 'dataset'}
        except KeyError as e:
            raise UnknownNode(dataset.collection, e.args[0])

        if force_dependent:
            nodes.update(x for name in selected_nodes
                         for x in persistent[name].dependent)
        nodes = sorted(nodes)

        storedir = app.site.config.marv.storedir
        store = Store(storedir, persistent)

        changed = False
        try:
            if nodes:
                changed = run_nodes(dataset, nodes, store, force=force,
                                    persistent=persistent,
                                    deps=deps, cachesize=cachesize)
        except:
            raise
        else:
            if changed or update_detail:
                collection.render_detail(dataset)
                log.verbose('%s detail rendered', setid)
            if changed or update_listing:
                collection.update_listings([dataset])
                log.verbose('%s listing rendered', setid)
        finally:
            if not keep:
                for tmpdir in store.pending.values():
                    store.logdebug('Cleaning up %r', tmpdir)
                    shutil.rmtree(tmpdir)
                store.pending.clear()

    def scan(self, dry_run=None):
        for collection in self.collections.values():
            for scanroot in collection.scanroots:
                collection.scan(scanroot, dry_run)

    def comment(self, username, message, ids):
        now = int(time.time() * 1000)
        comments = [Comment(dataset_id=id, author=username, time_added=now,
                            text=message)
                    for id in ids]
        db.session.add_all(comments)
        db.session.commit()

    def tag(self, setids, add=None, remove=None):
        assert setids
        assert add or remove, (add, remove)
        add = sorted(add or [])
        remove = remove or []
        addremove = set(add) | set(remove)
        assert len(addremove) == len(add) + len(remove), (add, remove)

        query = db.session.query(Dataset.collection, Dataset.id, Dataset.setid)\
                          .filter(Dataset.setid.in_(setids))\
                          .order_by(Dataset.collection)
        for collection, group in groupby(query, key=lambda x: x[0]):
            setidmap = {setid: id for _, id, setid in group}
            dataset_ids = setidmap.values()

            if add:
                stmt = Tag.__table__.insert().prefix_with('OR IGNORE')
                db.session.execute(stmt, [{'collection': collection,
                                           'value': x} for x in add])

            tags = {value: id for id, value in (
                db.session.query(Tag.id, Tag.value)
                .filter(Tag.collection == collection)
                .filter(Tag.value.in_(addremove)))}

            if add:
                stmt = dataset_tag.insert().prefix_with('OR IGNORE')
                db.session.execute(stmt,
                                   [{'dataset_id': x, 'tag_id': y} for x, y in
                                    product(dataset_ids, (tags[x] for x in add))])

            if remove:
                where = (dataset_tag.c.tag_id.in_(tags[x] for x in remove) &
                         dataset_tag.c.dataset_id.in_(dataset_ids))
                stmt = dataset_tag.delete().where(where)
                db.session.execute(stmt)

        db.session.commit()
