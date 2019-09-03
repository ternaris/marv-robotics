# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import inspect
import os
import random
import shutil
import tempfile
from itertools import count
from logging import getLogger

import pytest

import marv.model
from marv.db import scoped_session
from marv.site import Site


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


@pytest.fixture(scope='function')
async def site(loop):  # pylint: disable=unused-argument
    sitedir = tempfile.mkdtemp()
    scanroot = os.path.join(sitedir, 'scanroot')
    os.mkdir(scanroot)
    os.mkdir(os.path.join(scanroot, 'foo'))
    os.mkdir(os.path.join(scanroot, 'bar'))
    siteconf = os.path.join(sitedir, 'marv.conf')
    with open(siteconf, 'w') as fobj:
        fobj.write(inspect.cleandoc(CONFIG))

    prefix = f'test{next(COUNTER)}_'
    marv.model._LISTING_PREFIX = prefix  # pylint: disable=protected-access
    site_ = await Site.create(siteconf, init=True)
    site_.scanroot_ = scanroot
    yield site_

    async with scoped_session(site_.db) as connection:
        tables = await connection\
                .execute_query('SELECT name FROM sqlite_master WHERE type="table"')
        tables = (x['name'] for x in tables if x['name'].startswith(prefix))
        for table in sorted(tables, key=len, reverse=True):
            await connection.execute_query(f'DROP TABLE {table}')
    await site_.destroy()
    if not KEEP:
        shutil.rmtree(sitedir)
    else:
        print(f'Keeping {sitedir}')


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
    await site.db.update_tags_for_setids([foo1id, foo2id, bar1id], add=['a', 'b'], remove=[])
    await site.db.update_tags_for_setids([foo3id], add=['c'], remove=[])
    assert await site.db.list_tags() == ['a', 'b', 'c']
    assert await site.db.list_tags(collections=['foo']) == ['a', 'b', 'c']
    assert await site.db.list_tags(collections=['bar']) == ['a', 'b']

    # query tagged
    assert set(await site.db.query(tags=['a'])) == {foo1id, foo2id, bar1id}
    assert set(await site.db.query(tags=['b', 'c'])) == {foo1id, foo2id, foo3id, bar1id}

    # untag
    await site.db.update_tags_for_setids([foo1id, bar1id, bar2id], add=['x'], remove=['a', 'b'])
    assert await site.db.list_tags() == ['a', 'b', 'c', 'x']
    assert await site.db.list_tags(collections=['foo']) == ['a', 'b', 'c', 'x']
    assert await site.db.list_tags(collections=['bar']) == ['a', 'b', 'x']
    assert await site.db.query(path=foo1, tags=['a']) == []
    assert await site.db.query(path=foo2, tags=['a']) == [foo2id]
    await site.db.update_tags_for_setids([foo1id], add=[], remove=['x'])

    # cleanup tags
    await site.db.cleanup_tags()
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
