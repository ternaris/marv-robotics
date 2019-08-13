# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import json
import os
from itertools import count
from pathlib import Path

import mock
import pytest
import sqlalchemy as sqla

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
    'phjg4ncymwbrbl4yx35bciqazq',
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


def scanner(dirpath, dirnames, filenames):  # pylint: disable=unused-argument
    return [DatasetInfo(x, [x]) for x in filenames]


@marv.node(Int8Value)
@marv.input('dataset', default=dataset_node)
def node_test(dataset):
    dataset = yield marv.pull(dataset)
    with open(dataset.files[0].path) as f:
        yield marv.push({'value': int(f.read())})


@marv.node(Section)
@marv.input('node', default=node_test)
def section_test(node):
    value = yield marv.pull(node)
    value = value.value
    yield marv.push({'title': 'Test', 'widgets': [
        {'keyval': {'items': [{'title': 'value', 'cell': {'uint64': value}}]}},
    ]})


@pytest.fixture(scope='function')
def site(tmpdir):
    flag = (tmpdir / 'TEST_SITE')
    flag.write('')

    marv_conf = (tmpdir / 'marv.conf')
    marv_conf.write(MARV_CONF)

    # make scanroots
    for sitename in ('foo', 'bar'):
        for idx, name in enumerate(['a', '\u03a8']):
            name = f'{sitename}_{name}'
            path = tmpdir / 'scanroots' / sitename / name
            path.write(str(idx), ensure=True)

    yield Site(marv_conf.strpath, init=True)


@pytest.fixture(scope='function')
def app(site):  # pylint: disable=redefined-outer-name
    yield marv.app.create_app(site)


@pytest.fixture(scope='function')
async def client(aiohttp_client, app):  # pylint: disable=redefined-outer-name
    clt = await aiohttp_client(app)

    async def get_json(*args, **kw):
        resp = await clt.get(*args, **kw)
        return await resp.json()

    clt.get_json = get_json
    yield clt


def recorded(data, filename):
    """Assert data corresponds to recorded data.

    Record data if RECORD is set. Return True on success to enable
    being used as ``assert recorded()`` for nicer readability.

    """
    json_file = DATADIR / filename
    if RECORD:
        json_file.write_text(json.dumps(data, sort_keys=True, indent=2))
    recorded_data = json.loads(json_file.read_text())
    assert recorded_data == data, filename
    return True


async def test_dump(site, client):  # pylint: disable=redefined-outer-name  # noqa: C901
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements

    sitedir = os.path.dirname(site.config.filename)

    # Ensure all tables are empty / at factory defaults
    select = sqla.sql.select
    engine = sqla.create_engine(site.config.marv.dburi)
    meta = sqla.MetaData(engine)
    meta.reflect()
    con = engine.connect()
    tables = {
        k: v for k, v in meta.tables.items()
        if not k.startswith('listing_')
        if not k.startswith('sqlite_')
    }
    assert {
        'dataset', 'dataset_tag', 'tag', 'file', 'comment', 'user', 'user_group', 'group',
    } == tables.keys()
    for name, table in sorted(tables.items()):
        rows = list(con.execute(select([table])))
        if name == 'group':
            assert rows == [(1, 'admin')]
        else:
            assert not rows, name

    dump = dump_database(site.config.marv.dburi)
    assert recorded(dump, 'empty_dump.json')

    metadata = await client.get_json('/marv/api/meta')
    listings = {}
    for colinfo in metadata['collections']['items']:
        name = colinfo['id']
        listings[name] = await client.get_json(f'/marv/api/collection/{name}')
    assert recorded(listings, 'empty_listings.json')

    # Populate database, asserting in multiple ways that it is populated
    with mock.patch('marv_node.setid.SetID.random', side_effect=SETIDS) as _, \
            mock.patch('marv.utils.time', side_effect=count(2000)) as __, \
            mock.patch('marv.utils.mtime', side_effect=count(1000)):
        site.scan()

    with mock.patch('bcrypt.gensalt', return_value=b'$2b$12$k67acf6S32i3nW0c7ycwe.') as _, \
            mock.patch('marv.utils.time', side_effect=count(2000)):
        site.user_add('user1', 'pw1', 'marv', '')
        site.user_add('user2', 'pw2', 'marv', '')
    site.group_add('grp')
    site.group_adduser('admin', 'user1')
    site.group_adduser('grp', 'user2')

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
        data = await client.get_json(f'/marv/api/collection/{name}')
        rows = data['listing']['widget']['data']['rows']
        for row in sorted(rows, key=lambda x: x['setid']):
            del row['id']
            lst.append(row)
    assert recorded(listings, 'full_listings.json')

    details = []
    for colname, rows in sorted(listings.items()):
        for row in rows:
            detail = await client.get_json(f'/marv/api/dataset/{row["setid"]}')
            del detail['id']
            assert detail['collection'] == colname
            details.append(detail)
    assert recorded(details, 'full_details.json')

    # Dump database
    dump = dump_database(site.config.marv.dburi)
    for datasets in dump['datasets'].values():
        for dataset in datasets:
            for file in dataset['files']:
                file['path'] = file['path'].replace(sitedir, 'SITEDIR')
    assert recorded(dump, 'full_dump.json')


async def test_restore(client, site):  # pylint: disable=redefined-outer-name  # noqa: C901
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements

    sitedir = os.path.dirname(site.config.filename)

    # Ensure all tables are empty / at factory defaults
    select = sqla.sql.select
    engine = sqla.create_engine(site.config.marv.dburi)
    meta = sqla.MetaData(engine)
    meta.reflect()
    con = engine.connect()
    tables = {
        k: v for k, v in meta.tables.items()
        if not k.startswith('listing_')
        if not k.startswith('sqlite_')
    }
    assert {
        'dataset', 'dataset_tag', 'tag', 'file', 'comment', 'user', 'user_group', 'group',
    } == tables.keys()
    for name, table in sorted(tables.items()):
        rows = list(con.execute(select([table])))
        if name == 'group':
            assert rows == [(1, 'admin')]
        else:
            assert not rows, name

    dump = dump_database(site.config.marv.dburi)
    assert recorded(dump, 'empty_dump.json')

    metadata = await client.get_json('/marv/api/meta')
    listings = {}
    for colinfo in metadata['collections']['items']:
        name = colinfo['id']
        listings[name] = await client.get_json(f'/marv/api/collection/{name}')
    assert recorded(listings, 'empty_listings.json')

    # Restore database
    full_dump = json.loads((DATADIR / 'full_dump.json').read_text())
    for datasets in full_dump['datasets'].values():
        for dataset in datasets:
            for file in dataset['files']:
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
        data = await client.get_json(f'/marv/api/collection/{name}')
        rows = data['listing']['widget']['data']['rows']
        for row in sorted(rows, key=lambda x: x['setid']):
            del row['id']
            lst.append(row)
    assert recorded(listings, 'full_listings.json')

    # Assert detail is still the same
    details = []
    for colname, rows in sorted(listings.items()):
        for row in rows:
            detail = await client.get_json(f'/marv/api/dataset/{row["setid"]}')
            del detail['id']
            assert detail['collection'] == colname
            details.append(detail)
    assert recorded(details, 'full_details.json')

    # Redump database and assert dumps are the same
    dump = dump_database(site.config.marv.dburi)
    dump = json.loads(json.dumps(dump))
    full_dump = json.loads((DATADIR / 'full_dump.json').read_text())
    for datasets in full_dump['datasets'].values():
        for dataset in datasets:
            for file in dataset['files']:
                file['path'] = file['path'].replace('SITEDIR', sitedir)
    assert full_dump == dump
