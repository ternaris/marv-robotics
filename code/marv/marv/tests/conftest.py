# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import random
from itertools import count
from logging import getLogger
from pathlib import Path

import mock
import pytest

import marv
import marv.model
from marv.app import create_app
from marv.site import Site
from marv.types import Int8Value, Section, Words
from marv_nodes import dataset as dataset_node


log = getLogger(__name__)


COLLECTION_CONF = """
[collection {name}]
scanner = marv.tests.conftest:scanner
scanroots = ./scanroots/{name}
nodes =
    marv_nodes:dataset
    marv_nodes:meta_table
    marv_nodes:summary_keyval
    marv.tests.conftest:node_divisors
{add_nodes}

filters =
    name       | Name       | substring         | string   | (get "dataset.name")
    setid      | Set Id     | startswith        | string   | (get "dataset.id")
    size       | Size       | lt le eq ne ge gt | filesize | (sum (get "dataset.files[:].size"))
    status     | Status     | any all           | subset   | (status )
    tags       | Tags       | any all           | subset   | (tags )
    comments   | Comments   | substring         | string   | (comments )
    files      | File paths | substring_any     | string[] | (get "dataset.files[:].path")
    time_added | Added      | lt le eq ne ge gt | datetime | (get "dataset.time_added")
    time_mtime | Mtime      | lt le eq ne ge gt | datetime | (get "dataset.files[0].mtime")
    divisors   | Divisors   | any all           | subset   | (get "node_divisors.words")
{add_filters}

listing_columns =
    name       | Name     | route    | (detail_route (get "dataset.id") (get "dataset.name"))
    size       | Size     | filesize | (sum (get "dataset.files[:].size"))
    status     | Status   | icon[]   | (status )
    tags       | Tags     | pill[]   | (tags )
    time_added | Added    | datetime | (get "dataset.time_added")
    time_mtime | Mtime    | datetime | (get "dataset.files[0].mtime")
    #divisors   | Divisors | string   | (get "node_divisors.words")
{add_columns}

detail_sections =
{add_sections}
"""


MARV_CONF = """
[marv]
acl = marv_webapi.acls:public
collections = {collection_names}

{collections}
"""


def scanner(directory, subdirs, filenames):  # pylint: disable=unused-argument
    root = Path(directory).name
    return [
        (f'{root}_{x}_filtér' if x == '0043' else f'{root}_{x}', [x])
        for x in filenames
    ]


@marv.node(Int8Value)
@marv.input('dataset', default=dataset_node)
def node_test(dataset):
    dataset = yield marv.pull(dataset)
    filename = Path(dataset.files[0].path).name
    yield marv.push({'value': int(filename)})


@marv.node(Words)
@marv.input('dataset', default=dataset_node)
def node_divisors(dataset):
    dataset = yield marv.pull(dataset)
    filename = Path(dataset.files[0].path).name
    idx = int(filename)
    divisors = [
        x for x in range(1, idx + 1)
        if idx % x == 0
    ]
    yield marv.push({'words': [f'div{x}' for x in divisors]})


@marv.node(Section)
@marv.input('node', default=node_test)
def section_test(node):
    value = yield marv.pull(node)
    value = value.value
    yield marv.push({'title': 'Test', 'widgets': [
        {'keyval': {'items': [{'title': 'value', 'cell': {'uint64': value}}]}},
    ]})


@pytest.fixture(scope='function')
async def site(loop, tmpdir):  # pylint: disable=unused-argument
    collection_names = ('hodge', 'podge')
    add_nodes = (
        '    marv.tests.conftest:node_test\n'
        '    marv.tests.conftest:section_test\n'
    )
    add_filters = '    node_test | Test node | any | subset | (list (get "node_test.value" 0))'
    add_columns = '    node_test  | Test   | int      | (get "node_test.value" 0)'
    add_sections = '    section_test'
    collections = ''.join([
        COLLECTION_CONF.format(name='hodge',
                               add_nodes=add_nodes,
                               add_filters=add_filters,
                               add_columns=add_columns,
                               add_sections=add_sections),
        COLLECTION_CONF.format(name='podge',
                               add_nodes='',
                               add_filters='',
                               add_columns='',
                               add_sections=''),
    ])
    marv_conf = (tmpdir / 'marv.conf')
    marv_conf.write(MARV_CONF.format(collection_names=' '.join(collection_names),
                                     collections=collections))

    site = await Site.create(str(marv_conf), init=True)  # pylint: disable=redefined-outer-name
    await site.db.user_add('test', password='test_pw', realm='marv', realmuid='')
    await site.db.user_add('adm', password='adm_pw', realm='marv', realmuid='')
    await site.db.group_adduser(groupname='admin', username='adm')

    def walker(path):
        collection = Path(path).name
        assert collection in collection_names, 'TEST SETUP ERROR: basename must match a collection!'
        idx = collection_names.index(collection)
        return ((path, [], [f'{x+1:04d}' for x in range((idx + 1) * 50)]),)

    def stat(path):
        filename = Path(path).name
        idx = int(filename)

        class Stat:  # pylint: disable=too-few-public-methods
            st_mtime = 1500000000 + idx * 1000
            st_size = idx
        return Stat()

    try:
        with mock.patch('marv.utils.mtime', side_effect=count(1200000000)),\
             mock.patch('marv.utils.stat', wraps=stat),\
             mock.patch('marv.utils.now', side_effect=count(1400000000, 12 * 3600)),\
             mock.patch('marv.utils.walk', wraps=walker),\
             mock.patch('os.path.isdir', return_value=True):
            random.seed(42)
            await site.scan()
        yield site
    finally:
        await site.destroy()


@pytest.fixture(scope='function')
def app(site):  # pylint: disable=redefined-outer-name
    app_ = create_app(site)
    app_.on_shutdown.clear()
    yield app_


@pytest.fixture(scope='function')
async def client(aiohttp_client, app):  # pylint: disable=redefined-outer-name
    client = await aiohttp_client(app)  # pylint: disable=redefined-outer-name

    headers = {
        'Content-Type': 'application/json',
    }

    async def authenticate(username, password):
        if 'Authorization' in headers:
            del headers['Authorization']
        resp = await client.post_json('/marv/api/auth', json={
            'username': username,
            'password': password,
        })
        headers['Authorization'] = f'Bearer {resp["access_token"]}'

    async def get_json(*args, **kw):
        resp = await client.get(*args, headers=headers, **kw)
        return await resp.json()

    async def post_json(*args, **kw):
        resp = await client.post(*args, headers=headers, **kw)
        return await resp.json()

    client.headers = headers
    client.authenticate = authenticate
    client.get_json = get_json
    client.post_json = post_json
    yield client
