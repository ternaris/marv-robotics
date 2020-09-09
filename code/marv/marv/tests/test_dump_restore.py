# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import json
from pathlib import Path

import pytest

from .conftest import recorded

DATADIR = Path(__file__).parent / 'data'


async def prescan(site):
    await site.db.group_add('grp')
    await site.db.group_adduser('admin', 'adm')
    await site.db.group_adduser('grp', 'test')


async def postscan(site):
    hodgeids = await site.db.query(['hodge'])
    podgeids = await site.db.query(['podge'])
    await site.db.update_tags_by_setids(hodgeids, add=['TAG1'], remove=[])
    await site.db.update_tags_by_setids([hodgeids[1], podgeids[1]], add=['TAG2'], remove=[])
    await site.db.comment_by_setids([hodgeids[0]], 'test', 'comment\ntext')
    await site.db.comment_by_setids([hodgeids[1], podgeids[1]], 'adm', 'more\ncomment')


@pytest.mark.marv(site={'empty': True})
async def test_dump_empty(site):
    dump = await site.Database.dump_database(site.config.marv.dburi)
    assert recorded(dump, DATADIR / 'empty_dump.json')


@pytest.mark.marv(site={'prescan': prescan, 'postscan': postscan, 'size': 2})
async def test_dump(site):
    dump = await site.Database.dump_database(site.config.marv.dburi)
    assert recorded(dump, DATADIR / 'full_dump.json')


@pytest.mark.marv(site={'empty': True})
async def test_restore(site):
    full_dump = json.loads((DATADIR / 'full_dump.json').read_text())
    await site.restore_database(**full_dump)

    dump = await site.Database.dump_database(site.config.marv.dburi)
    dump = json.loads(json.dumps(dump))
    full_dump = json.loads((DATADIR / 'full_dump.json').read_text())
    assert full_dump == dump
