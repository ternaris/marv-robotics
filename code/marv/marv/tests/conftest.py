# Copyright 2016 - 2021  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import datetime
import json
import os
from itertools import count
from logging import getLogger
from pathlib import Path
from unittest import mock

import pytest

import marv.model
import marv_api as marv
from marv.app import App
from marv.site import Site
from marv_api.types import Int8Value, Section, Words
from marv_nodes import dataset as dataset_node

log = getLogger(__name__)


COLLECTION_CONF = """
[collection {name}]
scanner = marv.tests.conftest:scanner
scanroots = /dev/null/{name}
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
    status     | Status     | any all           | subset   | (status)
    tags       | Tags       | any all           | subset   | (tags)
    comments   | Comments   | substring         | string   | (comments)
    files      | File paths | substring_any     | string[] | (get "dataset.files[:].path")
    time_added | Added      | lt le eq ne ge gt | datetime | (get "dataset.time_added")
    time_mtime | Mtime      | lt le eq ne ge gt | datetime | (get "dataset.files[0].mtime")
    divisors   | Divisors   | any all           | subset   | (get "node_divisors.words")
{add_filters}

listing_columns =
    name       | Name     | route    | (detail_route (get "dataset.id") (get "dataset.name"))
    size       | Size     | filesize | (sum (get "dataset.files[:].size"))
    status     | Status   | icon[]   | (status)
    tags       | Tags     | pill[]   | (tags)
    time_added | Added    | datetime | (get "dataset.time_added")
    time_mtime | Mtime    | datetime | (get "dataset.files[0].mtime")
    #divisors   | Divisors | string   | (get "node_divisors.words")
{add_columns}

detail_sections =
{add_sections}
"""


MARV_CONF = """
[marv]
ce_anonymous_readonly_access = {anon_read}
collections = {collection_names}

{collections}
"""


def recorded(data, path):
    """Assert data corresponds to recorded data.

    Record data if RECORD is set. Return True on success to enable
    being used as ``assert recorded()`` for nicer readability.

    """
    if os.environ.get('MARV_TESTING_RECORD'):
        path.write_text(json.dumps(data, sort_keys=True, indent=2))
    recorded_data = json.loads(path.read_text())
    assert recorded_data == data, path
    return True


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


@pytest.fixture
async def site(loop, request, tmpdir):  # pylint: disable=unused-argument  # noqa: C901
    # pylint: disable=too-many-locals
    collection_names = ('hodge', 'podge')
    add_nodes = '\n'.join([
        '    marv.tests.conftest:node_test',
        '    marv.tests.conftest:section_test',
    ])
    add_filters = '    node_test | Test node | any | subset' + \
        ' | (filter null (makelist (get "node_test.value" 0)))'
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
    mark = {x.name: x.kwargs for x in request.node.iter_markers()}
    site_cfg = mark.get('marv', {}).get('site', {})
    marv_conf.write(MARV_CONF.format(anon_read=site_cfg.get('acl') == 'marv_webapi.acls:public',
                                     collection_names=' '.join(collection_names),
                                     collections=collections))

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
                ret = vanilla_datetime.utcfromtimestamp(next(side_effect))
                return ret

        return DatetimeMeta('datetime', (DatetimeBase,), {})

    def walker(path):
        collection = Path(path).name
        assert collection in collection_names, 'TEST SETUP ERROR: basename must match a collection!'
        idx = collection_names.index(collection)
        size = site_cfg.get('size', 10)
        return ((path, [], [f'{x+1:04d}' for x in range((idx + 1) * size)]),)

    def stat(path):
        filename = Path(path).name
        idx = int(filename)

        class Stat:  # pylint: disable=too-few-public-methods
            st_mtime = 1500000000 + idx * 1000
            st_size = idx
        return Stat()

    class Bcrypt:
        PWDB = {
            b'adm_pw': b'bs1QyNuPObrtRc0M8h71kIhNli0COLC',
            b'test_pw': b'iB5fVFuFzQLmNLdZtYldTg9VvVFZDe2',
        }

        @staticmethod
        def gensalt():
            return b'$2b$12$k67acf6S32i3nW0c7ycwe.'

        @staticmethod
        def hashpw(password, salt):
            return salt + Bcrypt.PWDB.get(password, b'')

        @staticmethod
        def checkpw(clear, hashed):
            return Bcrypt.gensalt() + Bcrypt.PWDB.get(clear, b'') == hashed

    cls = site_cfg.get('cls', Site)
    site = await cls.create(marv_conf, init=True)  # pylint: disable=redefined-outer-name
    try:
        if not site_cfg.get('empty'):
            with mock.patch('marv.db.bcrypt', wraps=Bcrypt), \
                    mock.patch.object(datetime, 'datetime', create_datemock()), \
                    mock.patch('marv_api.setid.SetID.random', side_effect=count(2**127)), \
                    mock.patch('marv.utils.mtime', side_effect=count(1200000000)), \
                    mock.patch('marv.utils.stat', wraps=stat), \
                    mock.patch('marv.utils.now', side_effect=count(1400000000, 12 * 3600)), \
                    mock.patch('marv.utils.walk', wraps=walker), \
                    mock.patch('os.path.isdir', return_value=True), \
                    mock.patch('secrets.choice', return_value='#'):
                await site.db.user_add('test', password='test_pw', realm='marv', realmuid='',
                                       time_created=0xdead0001, time_updated=0xdead0002)
                await site.db.user_add('adm', password='adm_pw', realm='marv', realmuid='',
                                       time_created=0xdead0003, time_updated=0xdead0004)
                await site.db.group_adduser(groupname='admin', username='adm')

                prescan = site_cfg.get('prescan', None)
                if prescan:
                    await prescan(site)
                await site.scan()
                postscan = site_cfg.get('postscan', None)
                if postscan:
                    await postscan(site)

        yield site
    finally:
        await site.destroy()


@pytest.fixture
def app(site, request):  # pylint: disable=redefined-outer-name
    mark = {x.name: x.kwargs for x in request.node.iter_markers()}
    app_cfg = mark.get('marv', {}).get('app', {})
    cls = app_cfg.get('cls', App)
    app_ = cls(site).aioapp
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

    async def unauthenticate():
        return headers.pop('Authorization', '')

    async def get_json(*args, **kw):
        resp = await client.get(*args, headers=headers, **kw)
        if resp.status < 300 and resp.headers['content-type'].startswith('application/json'):
            return await resp.json()
        return resp

    async def post_json(*args, **kw):
        resp = await client.post(*args, headers=headers, **kw)
        if resp.status < 300 and resp.headers['content-type'].startswith('application/json'):
            return await resp.json()
        return resp

    client.headers = headers
    client.authenticate = authenticate
    client.get_json = get_json
    client.post_json = post_json
    client.unauthenticate = unauthenticate
    yield client
