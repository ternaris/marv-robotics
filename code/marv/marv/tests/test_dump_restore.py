# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import datetime
import json
import os
from itertools import count
from pathlib import Path

import mock
import pytest
from tortoise.transactions import in_transaction

import marv
import marv.app
from marv.db import dump_database
from marv.scanner import DatasetInfo
from marv.site import Site
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


def create_datemock():
    vanilla_datetime = datetime.datetime
    side_effect = count(6000)

    class DatetimeMeta(type):
        @classmethod
        def __instancecheck__(cls, obj):
            return isinstance(obj, vanilla_datetime)

    class DatetimeBase(vanilla_datetime):
        @classmethod
        def utcnow(cls):
            ret = vanilla_datetime.fromtimestamp(next(side_effect))
            return ret

    return DatetimeMeta('datetime', (DatetimeBase,), {})


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
async def site(tmpdir):
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

    yield await Site.create(marv_conf.strpath, init=True)


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
    async with in_transaction() as connection:
        query = 'SELECT name FROM sqlite_master WHERE type="table"'
        tables = [
            x['name'] for x in await connection.execute_query(query)
            if not x['name'].startswith('l_')
            if not x['name'].startswith('sqlite_')
        ]
        assert {
            'dataset', 'dataset_tag', 'tag', 'file', 'comment', 'user', 'user_group', 'group',
        } == set(tables)
        for name in sorted(tables):
            rows = list(await connection.execute_query(f'SELECT * FROM "{name}";'))
            if name == 'group':
                assert rows == [{'id': 1, 'name': 'admin'}]
            else:
                assert not rows, name

    dump = await dump_database(site.config.marv.dburi)
    assert recorded(dump, 'empty_dump.json')

    metadata = await client.get_json('/marv/api/meta')
    listings = {}
    for colinfo in metadata['collections']['items']:
        name = colinfo['id']
        listings[name] = await client.get_json(f'/marv/api/collection/{name}')
    assert recorded(listings, 'empty_listings.json')

    # Populate database, asserting in multiple ways that it is populated
    with mock.patch('marv_node.setid.SetID.random', side_effect=SETIDS) as _, \
            mock.patch('marv.utils.mtime', side_effect=count(1000)) as __, \
            mock.patch('marv.utils.now', side_effect=count(1)):
        await site.scan()

    with mock.patch('bcrypt.gensalt', return_value=b'$2b$12$k67acf6S32i3nW0c7ycwe.') as _, \
            mock.patch.object(datetime, 'datetime', create_datemock()):
        await site.db.user_add('user1', 'pw1', 'marv', '', time_created=4201, time_updated=4202)
        await site.db.user_add('user2', 'pw2', 'marv', '', time_created=4203, time_updated=4204)
    await site.db.group_add('grp')
    await site.db.group_adduser('admin', 'user1')
    await site.db.group_adduser('grp', 'user2')

    fooids = await site.db.query(['foo'])
    barids = await site.db.query(['bar'])
    await site.db.update_tags_for_setids(fooids, add=['TAG1'], remove=[])
    await site.db.update_tags_for_setids([fooids[1], barids[1]], add=['TAG2'], remove=[])

    with mock.patch('marv.utils.now', side_effect=count(100000)):
        await site.db.comment_multiple([fooids[0]], 'user1', 'comment\ntext')
        await site.db.comment_multiple([fooids[1], barids[1]], 'user2', 'more\ncomment')

    async with in_transaction() as connection:
        # Ensure all tables have been populated
        query = 'SELECT name FROM sqlite_master WHERE type="table"'
        tables = [
            x['name'] for x in (await connection.execute_query(query))
            if not x['name'].startswith('l_')
        ]
        for name in sorted(tables):
            rows = list(await connection.execute_query(f'SELECT * FROM "{name}"'))
            if name == 'group':
                assert len(rows) > 1
            else:
                assert rows, name

    # Run nodes
    for setid in fooids + barids:
        changed = await site.run(setid)
        assert len(changed) == 5
        changed = await site.run(setid)
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
    dump = await dump_database(site.config.marv.dburi)
    for datasets in dump['datasets'].values():
        for dataset in datasets:
            for file in dataset['files']:
                file['path'] = file['path'].replace(sitedir, 'SITEDIR')
    assert recorded(dump, 'full_dump.json')


async def test_restore(client, site):  # pylint: disable=redefined-outer-name  # noqa: C901
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements

    sitedir = os.path.dirname(site.config.filename)

    # Ensure all tables are empty / at factory defaults
    async with in_transaction() as connection:
        query = 'SELECT name FROM sqlite_master WHERE type="table"'
        tables = [
            x['name'] for x in await connection.execute_query(query)
            if not x['name'].startswith('l_')
            if not x['name'].startswith('sqlite_')
        ]
        assert {
            'dataset', 'dataset_tag', 'tag', 'file', 'comment', 'user', 'user_group', 'group',
        } == set(tables)
        for name in sorted(tables):
            rows = list(await connection.execute_query(f'SELECT * FROM "{name}";'))
            if name == 'group':
                assert rows == [{'id': 1, 'name': 'admin'}]
            else:
                assert not rows, name

    dump = await dump_database(site.config.marv.dburi)
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
    await site.restore_database(**full_dump)

    # Ensure all tables have been populated
    async with in_transaction() as connection:
        query = 'SELECT name FROM sqlite_master WHERE type="table"'
        tables = [
            x['name'] for x in (await connection.execute_query(query))
            if not x['name'].startswith('l_')
        ]
        for name in sorted(tables):
            rows = list(await connection.execute_query(f'SELECT * FROM "{name}"'))
            if name == 'group':
                assert len(rows) > 1
            else:
                assert rows, name

    # Run nodes
    fooids = await site.db.query(['foo'])
    barids = await site.db.query(['bar'])
    for setid in fooids + barids:
        changed = await site.run(setid)
        assert len(changed) == 5
        changed = await site.run(setid)
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
    dump = await dump_database(site.config.marv.dburi)
    dump = json.loads(json.dumps(dump))
    full_dump = json.loads((DATADIR / 'full_dump.json').read_text())
    for datasets in full_dump['datasets'].values():
        for dataset in datasets:
            for file in dataset['files']:
                file['path'] = file['path'].replace('SITEDIR', sitedir)
    assert full_dump == dump
