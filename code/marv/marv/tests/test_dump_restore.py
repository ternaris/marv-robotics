# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import json
import os
from itertools import count

import mock
import pytest
import sqlalchemy as sqla
from flask import current_app
from pathlib2 import Path

import marv
import marv.app
from marv.scanner import DatasetInfo
from marv.site import Site, dump_database
from marv.types import Int8Value, Section
from marv_nodes import dataset as dataset_node


DATADIR = Path(__file__).parent / 'data'
RECORD = os.environ.get('MARV_TESTING_RECORD')
SETIDS = [
    'l2vnfhfoe3z7ad7vclkd64tsqy',
    'vdls3sgw5yanuat4uepmhjwcpm',
    'e2oxlhpedjwked2llnnzir4tii',
    'phjg4ncymwbrbl4yx35bciqazq'
]

MARV_CONF = """
[marv]
acl = marv_webapi.acls:public
collections = foo bar

[collection foo]
scanner = marv.tests.test_dump_restore:scanner
scanroots = ./scanroots/foo
nodes =
    marv_nodes:dataset
    marv_nodes:meta_table
    marv_nodes:summary_keyval
    marv.tests.test_dump_restore:node_test
    marv.tests.test_dump_restore:section_test
filters =
    name       | Name       | substring         | string   | (get "dataset.name")
    setid      | Set Id     | startswith        | string   | (get "dataset.id")
    size       | Size       | lt le eq ne ge gt | filesize | (sum (get "dataset.files[:].size"))
    status     | Status     | any all           | subset   | (status )
    tags       | Tags       | any all           | subset   | (tags )
    comments   | Comments   | substring         | string   | (comments )
    files      | File paths | substring_any     | string[] | (get "dataset.files[:].path")
    time_added | Added      | lt le eq ne ge gt | datetime | (get "dataset.time_added")
    node_test  | Test node  | any               | subset   | (list (get "node_test.value" 0))
listing_columns =
    name       | Name   | route    | (detail_route (get "dataset.id") (get "dataset.name"))
    size       | Size   | filesize | (sum (get "dataset.files[:].size"))
    status     | Status | icon[]   | (status )
    tags       | Tags   | pill[]   | (tags )
    time_added | Added  | datetime | (get "dataset.time_added")
    node_test  | Test   | int      | (get "node_test.value" 0)
detail_sections =
    section_test

[collection bar]
scanner = marv.tests.test_dump_restore:scanner
scanroots = ./scanroots/bar
nodes =
    marv_nodes:dataset
    marv_nodes:meta_table
    marv_nodes:summary_keyval
    marv.tests.test_dump_restore:node_test
    marv.tests.test_dump_restore:section_test
filters =
    name       | Name       | substring         | string   | (get "dataset.name")
    setid      | Set Id     | startswith        | string   | (get "dataset.id")
    size       | Size       | lt le eq ne ge gt | filesize | (sum (get "dataset.files[:].size"))
    status     | Status     | any all           | subset   | (status )
    tags       | Tags       | any all           | subset   | (tags )
    comments   | Comments   | substring         | string   | (comments )
    files      | File paths | substring_any     | string[] | (get "dataset.files[:].path")
    time_added | Added      | lt le eq ne ge gt | datetime | (get "dataset.time_added")
    node_test  | Test node  | any               | subset   | (list (get "node_test.value" 0))
listing_columns =
    name       | Name   | route    | (detail_route (get "dataset.id") (get "dataset.name"))
    size       | Size   | filesize | (sum (get "dataset.files[:].size"))
    status     | Status | icon[]   | (status )
    tags       | Tags   | pill[]   | (tags )
    time_added | Added  | datetime | (get "dataset.time_added")
    node_test  | Test   | int      | (get "node_test.value" 0)
detail_sections =
    section_test
"""


def scanner(dirpath, dirnames, filenames):
    return [DatasetInfo(x, [x]) for x in filenames]


@marv.node(Int8Value)
@marv.input('dataset', default=dataset_node)
def node_test(dataset):
    dataset = yield marv.pull(dataset)
    with open(dataset.files[0].path) as f:
        yield marv.push({'value': int(f.read())})


@marv.node(Section)
@marv.input('node_test', default=node_test)
def section_test(node_test):
    value = yield marv.pull(node_test)
    value = value.value
    yield marv.push({'title': 'Test', 'widgets': [
        {'keyval': {'items': [{'title': 'value', 'cell': {'uint64': value}}]}}
    ]})


@pytest.fixture(scope='function')
def site(tmpdir):
    flag = (tmpdir / 'TEST_SITE')
    flag.write('')

    marv_conf = (tmpdir / 'marv.conf')
    marv_conf.write(MARV_CONF)

    # make scanroots
    for sitename in ('foo', 'bar'):
        for idx, name in enumerate(['a', u'\u03a8'.encode('utf-8')]):
            name = '{}_{}'.format(sitename, name)
            path = tmpdir / 'scanroots' / sitename / name
            path.write(str(idx), ensure=True)

    yield Site(marv_conf.strpath)


@pytest.fixture(scope='function')
def app(site):
    app = marv.app.create_app(site, init=True)
    app.testing = True
    with app.app_context():
        app = app.test_client()
        def get_json(*args, **kw):
            resp = app.get(*args, **kw)
            return json.loads(resp.data)
        app.get_json = get_json
        yield app


def recorded(data, filename):
    """Assert data corresponds to recorded data.

    Record data if RECORD is set. Return True on success to enable
    being used as ``assert recorded()`` for nicer readability.

    """
    json_file = DATADIR / filename
    if RECORD:
        json_file.write_bytes(json.dumps(data, sort_keys=True, indent=2))
    recorded_data = json.loads(json_file.read_bytes())
    assert recorded_data == data, filename
    return True


def test_dump(app, site):
    sitedir = os.path.dirname(site.config.filename)

    # Ensure all tables are empty / at factory defaults
    select = sqla.sql.select
    engine = sqla.create_engine(site.config.marv.dburi)
    meta = sqla.MetaData(engine)
    meta.reflect()
    con = engine.connect()
    tables = {k: v for k, v in meta.tables.items() if not k.startswith('listing_')}
    assert tables.viewkeys() == \
        {'dataset', 'dataset_tag', 'tag', 'file', 'comment', 'user', 'user_group', 'group'}
    for name, table in sorted(tables.items()):
        rows = list(con.execute(select([table])))
        if name == 'group':
            assert rows == [(1, 'admin')]
        else:
            assert not rows, name

    dump = dump_database(site.config.marv.dburi)
    assert recorded(dump, 'empty_dump.json')

    metadata = app.get_json('/marv/api/meta')
    listings = {}
    for colinfo in metadata['collections']['items']:
        name = colinfo['id']
        listings[name] = app.get_json('/marv/api/collection/{}'.format(name))
    assert recorded(listings, 'empty_listings.json')

    # Populate database, asserting in multiple ways that it is populated
    with mock.patch('marv_node.setid.SetID.random', side_effect=SETIDS) as _, \
         mock.patch('marv.utils.time', side_effect=count(2000)) as __, \
         mock.patch('marv.utils.mtime', side_effect=count(1000)):
        site.scan()
    um = current_app.um

    with mock.patch('bcrypt.gensalt', return_value='$2b$12$k67acf6S32i3nW0c7ycwe.') as _, \
         mock.patch('marv.utils.time', side_effect=count(2000)):
        um.user_add('user1', 'pw1', 'marv', '')
        um.user_add('user2', 'pw2', 'marv', '')
    um.group_add('grp')
    um.group_adduser('admin', 'user1')
    um.group_adduser('grp', 'user2')

    fooids = site.query(['foo'])
    barids = site.query(['bar'])
    site.tag(fooids, add=['TAG1'])
    site.tag([fooids[1], barids[1]], add=['TAG2'])

    fooid0 = con.execute('SELECT id FROM dataset WHERE setid = $1', fooids[0]).scalar()
    fooid1 = con.execute('SELECT id FROM dataset WHERE setid = $1', fooids[1]).scalar()
    barid1 = con.execute('SELECT id FROM dataset WHERE setid = $1', barids[1]).scalar()
    with mock.patch('marv.utils.now', side_effect=count(100000)):
        site.comment('user1', 'comment\ntext', [fooid0])
        site.comment('user2', 'more\ncomment', [fooid1, barid1])

    # Ensure all tables have been populated
    tables = {k: v for k, v in meta.tables.items() if not k.startswith('listing_')}
    for name, table in sorted(tables.items()):
        rows = list(con.execute(select([table])))
        if name == 'group':
            assert len(rows) > 1
        else:
            assert rows, name

    # Run nodes
    for setid in fooids + barids:
        changed = site.run(setid)
        assert len(changed) == 5
        changed = site.run(setid)
        assert not changed

    listings = {}
    for colinfo in metadata['collections']['items']:
        name = colinfo['id']
        listings[name] = lst = []
        data = app.get_json('/marv/api/collection/{}'.format(name))
        rows = data['listing']['widget']['data']['rows']
        for row in sorted(rows, key=lambda x: x['setid']):
            del row['id']
            lst.append(row)
    assert recorded(listings, 'full_listings.json')

    details = []
    for colname, rows in sorted(listings.items()):
        for row in rows:
            detail = app.get_json('/marv/api/dataset/{}'.format(row['setid']))
            del detail['id']
            assert detail['collection'] == colname
            details.append(detail)
    assert recorded(details, 'full_details.json')

    # Dump database
    dump = dump_database(site.config.marv.dburi)
    for datasets in dump['datasets'].values():
        for ds in datasets:
            for file in ds['files']:
                file['path'] = file['path'].replace(sitedir, 'SITEDIR')
    assert recorded(dump, 'full_dump.json')


def test_restore(app, site):
    sitedir = os.path.dirname(site.config.filename)

    # Ensure all tables are empty / at factory defaults
    select = sqla.sql.select
    engine = sqla.create_engine(site.config.marv.dburi)
    meta = sqla.MetaData(engine)
    meta.reflect()
    con = engine.connect()
    tables = {k: v for k, v in meta.tables.items() if not k.startswith('listing_')}
    assert tables.viewkeys() == \
        {'dataset', 'dataset_tag', 'tag', 'file', 'comment', 'user', 'user_group', 'group'}
    for name, table in sorted(tables.items()):
        rows = list(con.execute(select([table])))
        if name == 'group':
            assert rows == [(1, 'admin')]
        else:
            assert not rows, name

    dump = dump_database(site.config.marv.dburi)
    assert recorded(dump, 'empty_dump.json')

    metadata = app.get_json('/marv/api/meta')
    listings = {}
    for colinfo in metadata['collections']['items']:
        name = colinfo['id']
        listings[name] = app.get_json('/marv/api/collection/{}'.format(name))
    assert recorded(listings, 'empty_listings.json')

    # Restore database
    full_dump = json.loads((DATADIR / 'full_dump.json').read_bytes())
    for datasets in full_dump['datasets'].values():
        for ds in datasets:
            for file in ds['files']:
                file['path'] = file['path'].replace('SITEDIR', sitedir)
    site.restore_database(**full_dump)

    # Ensure all tables have been populated
    tables = {k: v for k, v in meta.tables.items() if not k.startswith('listing_')}
    for name, table in sorted(tables.items()):
        rows = list(con.execute(select([table])))
        if name == 'group':
            assert len(rows) > 1
        else:
            assert rows, name

    # Run nodes
    fooids = site.query(['foo'])
    barids = site.query(['bar'])
    for setid in fooids + barids:
        changed = site.run(setid)
        assert len(changed) == 5
        changed = site.run(setid)
        assert not changed

    # Assert listing is still the same
    listings = {}
    for colinfo in metadata['collections']['items']:
        name = colinfo['id']
        listings[name] = lst = []
        data = app.get_json('/marv/api/collection/{}'.format(name))
        rows = data['listing']['widget']['data']['rows']
        for row in sorted(rows, key=lambda x: x['setid']):
            del row['id']
            lst.append(row)
    assert recorded(listings, 'full_listings.json')

    # Assert detail is still the same
    details = []
    for colname, rows in sorted(listings.items()):
        for row in rows:
            detail = app.get_json('/marv/api/dataset/{}'.format(row['setid']))
            del detail['id']
            assert detail['collection'] == colname
            details.append(detail)
    assert recorded(details, 'full_details.json')

    # Redump database and assert dumps are the same
    dump = dump_database(site.config.marv.dburi)
    dump = json.loads(json.dumps(dump))
    full_dump = json.loads((DATADIR / 'full_dump.json').read_bytes())
    for datasets in full_dump['datasets'].values():
        for ds in datasets:
            for file in ds['files']:
                file['path'] = file['path'].replace('SITEDIR', sitedir)
    assert full_dump == dump
