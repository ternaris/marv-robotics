# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import os
from pathlib import Path

import pytest

import marv_api as marv
from marv.config import ConfigError
from marv.site import Site
from marv_api import DatasetInfo
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
collections = foo

[collection foo]
scanner = marv.tests.test_persist_without_type:scanner
scanroots = ./scanroots/foo
nodes =
    marv_nodes:dataset
    marv_nodes:summary_keyval
    marv_nodes:meta_table
    marv.tests.test_persist_without_type:notype
listing_columns =
    name       | Name   | route    | (detail_route (get "dataset.id") (get "dataset.name"))
    size       | Size   | filesize | (sum (get "dataset.files[:].size"))
    status     | Status | icon[]   | (status)
    tags       | Tags   | pill[]   | (tags)
    notype     | NoType | datetime | (get "notype.value")
"""


def scanner(dirpath, dirnames, filenames):  # pylint: disable=unused-argument
    return [DatasetInfo(x, [x]) for x in filenames]


@marv.node()
@marv.input('dataset', default=dataset_node)
def notype(dataset):
    dataset = yield marv.pull(dataset)
    with open(dataset.files[0].path) as f:
        yield marv.push({'value': int(f.read())})


@pytest.fixture
async def site(loop, tmpdir):  # pylint: disable=unused-argument
    flag = (tmpdir / 'TEST_SITE')
    flag.write('')

    marv_conf = (tmpdir / 'marv.conf')
    marv_conf.write(MARV_CONF)

    # make scanroots
    for sitename in ('foo',):
        for idx, name in enumerate(['a', 'b']):
            name = f'{sitename}_{name}'
            path = tmpdir / 'scanroots' / sitename / name
            path.write(str(idx), ensure=True)

    site_ = await Site.create(marv_conf, init=True)
    yield site_
    await site_.destroy()


async def test_fail_notype(site):  # pylint: disable=redefined-outer-name
    with pytest.raises(ConfigError):
        await site.scan()
