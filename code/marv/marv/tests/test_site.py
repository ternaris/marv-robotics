# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import inspect
import os
import random
import shutil
import tempfile
from itertools import count
from logging import getLogger
from pathlib import Path

import pytest

from marv.db import scoped_session
from marv.site import Site
from marv_api.utils import echo
from marv_node.testing import make_dataset, marv, run_nodes

KEEP = os.environ.get('KEEP')
log = getLogger(__name__)

CONFIG = """
[marv]
collections = foo bar

[collection foo]
scanner = marv.tests.test_site:scan_foo
scanroots = scanroot/foo

[collection bar]
scanner = marv.tests.test_site:scan_bar
scanroots = scanroot/bar
"""


def scan_foo(directory, subdirs, filenames):  # pylint: disable=unused-argument
    return [(os.path.basename(x), [x]) for x in filenames
            if x.endswith('.foo')]


def scan_bar(directory, subdirs, filenames):  # pylint: disable=unused-argument
    return [(os.path.basename(x), [x]) for x in filenames
            if x.endswith('.bar')]


COUNTER = count()


@pytest.fixture
async def site(loop):  # pylint: disable=unused-argument
    sitedir = tempfile.mkdtemp()
    scanroot = os.path.join(sitedir, 'scanroot')
    os.mkdir(scanroot)
    os.mkdir(os.path.join(scanroot, 'foo'))
    os.mkdir(os.path.join(scanroot, 'bar'))
    siteconf = os.path.join(sitedir, 'marv.conf')
    with open(siteconf, 'w') as fobj:
        fobj.write(inspect.cleandoc(CONFIG))

    site_ = await Site.create(Path(siteconf), init=True)
    site_.scanroot_ = scanroot
    (site_.config.marv.resourcedir / 'answer').write_text('42')

    yield site_

    async with scoped_session(site_.db) as connection:
        tables = (await connection
                  .execute_query('SELECT name FROM sqlite_master WHERE type="table"'))[1]
        tables = (x['name'] for x in tables if x['name'].startswith('l_'))
        for table in sorted(tables, key=len, reverse=True):
            await connection.execute_query(f'DROP TABLE {table}')
    await site_.destroy()
    if not KEEP:
        shutil.rmtree(sitedir)
    else:
        echo(f'Keeping {sitedir}')


def generate_foo(scanroot, name):
    filename = os.path.join(scanroot, 'foo', f'{name}.foo')
    with open(filename, 'w') as f:
        f.write('')
    log.verbose('wrote %s', filename)
    return filename


def generate_bar(scanroot, name):
    filename = os.path.join(scanroot, 'bar', f'{name}.bar')
    with open(filename, 'w') as f:
        f.write('')
    log.verbose('wrote %s', filename)
    return filename


async def test_collections(site):  # pylint: disable=redefined-outer-name
    collections = await site.db.get_collections('::')
    assert collections == [{'id': 2, 'name': 'bar'}, {'id': 1, 'name': 'foo'}]


async def test_flow_query_and_tag(site):  # pylint: disable=redefined-outer-name
    # init and scan empty
    await site.scan()
    assert await site.db.query() == []

    # generate some
    random.seed(42)
    foo1 = generate_foo(site.scanroot_, 'foo1')
    foo2 = generate_foo(site.scanroot_, 'foo2')
    bar1 = generate_bar(site.scanroot_, 'bar1')
    await site.scan()
    assert [str(x) for x in await site.db.query()] == ['k5jgqruqhoyt5xsweq46tqnyem',
                                                       'tv43di37ggabzui2m4dpwqgwxu',
                                                       'vfqitpfhd46ru3jnhsw3gzu4xu']

    # generate more and rescan
    foo3 = generate_foo(site.scanroot_, 'foo3')
    bar2 = generate_bar(site.scanroot_, 'bar2')
    await site.scan()
    assert len(await site.db.query()) == 5

    # get ids
    foo1id = (await site.db.query(path=foo1))[0]
    foo2id = (await site.db.query(path=foo2))[0]
    foo3id = (await site.db.query(path=foo3))[0]
    bar1id = (await site.db.query(path=bar1))[0]
    bar2id = (await site.db.query(path=bar2))[0]

    # query combinations
    assert set(await site.db.query(collections=['bar'])) == {bar1id, bar2id}
    assert await site.db.query(path=foo1[:-1]) == [foo1id]
    assert await site.db.query(collections=['bar'], path=foo1[:-1]) == []
    assert await site.db.query(collections=['foo', 'bar'], path=foo1) == [foo1id]

    # tag
    await site.db.update_tags_by_setids([foo1id, foo2id, bar1id], add=['a', 'b'], remove=[])
    await site.db.update_tags_by_setids([foo3id], add=['c'], remove=[])
    assert await site.db.list_tags() == ['a', 'b', 'c']
    assert await site.db.list_tags(collections=['foo']) == ['a', 'b', 'c']
    assert await site.db.list_tags(collections=['bar']) == ['a', 'b']

    # query tagged
    assert set(await site.db.query(tags=['a'])) == {foo1id, foo2id, bar1id}
    assert set(await site.db.query(tags=['b', 'c'])) == {foo1id, foo2id, foo3id, bar1id}

    # untag
    await site.db.update_tags_by_setids([foo1id, bar1id], add=['x'], remove=['a', 'b'])
    assert await site.db.list_tags() == ['a', 'b', 'c', 'x']
    assert await site.db.list_tags(collections=['foo']) == ['a', 'b', 'c', 'x']
    assert await site.db.list_tags(collections=['bar']) == ['x']
    assert await site.db.query(path=foo1, tags=['a']) == []
    assert await site.db.query(path=foo2, tags=['a']) == [foo2id]
    await site.db.update_tags_by_setids([foo1id], add=[], remove=['x'])

    # cleanup tags
    await site.db.delete_tag_values_without_ref()
    assert await site.db.list_tags() == ['a', 'b', 'c', 'x']
    assert await site.db.list_tags(collections=['foo']) == ['a', 'b', 'c']
    assert await site.db.list_tags(collections=['bar']) == ['x']

    # run nodes
    await site.run(foo1id)


async def test_outdated_node(site):  # pylint: disable=redefined-outer-name
    foo1 = generate_foo(site.scanroot_, 'foo1')
    await site.scan()
    foo1id = (await site.db.query(path=foo1))[0]
    assert foo1id


@marv.node()
def useresource():
    path = yield marv.get_resource_path('answer')
    yield marv.push(path.read_text())


DATASET = make_dataset()


async def test_node_site_resource(site):  # pylint: disable=redefined-outer-name
    nodes = [useresource]
    streams = await run_nodes(DATASET, nodes, site=site)
    assert streams == [
        ['42'],
    ]
