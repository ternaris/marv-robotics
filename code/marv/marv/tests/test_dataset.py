# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import pytest

from marv.db import MultipleSetidFound, NoSetidFound


async def test_id_helpers(site):
    assert not await site.db.resolve_shortids([])
    with pytest.raises(MultipleSetidFound):
        await site.db.resolve_shortids([''])
    with pytest.raises(NoSetidFound):
        await site.db.resolve_shortids(['@'])

    sets = await site.db.get_datasets_for_collections(None)
    setid1 = sets[0]
    setid20 = sets[19]

    assert await site.db.resolve_shortids(['aaaa']) == [setid1]
    assert await site.db.resolve_shortids(['aaaa', 'aaa']) == [setid1]
    assert await site.db.resolve_shortids(['aaaa', 'cmaa']) == sorted([setid1, setid20])

    res1 = await site.db.get_datasets_by_setids([setid1, setid20], [], '::')
    res2 = await site.db.get_datasets_by_dbids([1, 20], [], '::')
    assert {x.setid for x in res1} == {x.setid for x in res2}

    res1 = await site.db.get_datasets_by_setids([setid1, setid20], ['files'], '::')
    res2 = await site.db.get_datasets_by_dbids([1, 20], ['files'], '::')
    assert {x.files[0].path for x in res1} == {x.files[0].path for x in res2}


async def test_lookups(site):
    sets = await site.db.get_datasets_for_collections(None)
    assert len(sets) == 30

    sets = await site.db.get_datasets_for_collections(['hodge'])
    assert len(sets) == 10

    res = await site.db.get_filepath_by_setid_idx(sets[9], 0, '::')
    assert res.endswith('hodge/0010')


async def test_discard(site):
    sets = await site.db.get_datasets_for_collections(None)

    first = sets[0]
    await site.db.discard_datasets_by_setids([first])
    rest = await site.db.get_datasets_for_collections(None)
    assert set(sets) - set(rest) == {first}

    await site.db.discard_datasets_by_setids([first], False)
    rest = await site.db.get_datasets_for_collections(None)
    assert sets == rest

    await site.db.discard_datasets_by_dbids([1], True, '::')
    rest = await site.db.get_datasets_for_collections(None)
    assert set(sets) - set(rest) == {first}

    with pytest.raises(NoSetidFound):
        await site.db.resolve_shortids([first])

    res = await site.db.resolve_shortids([first], discarded=True)
    assert res == [first]

    await site.cleanup_discarded()
    with pytest.raises(NoSetidFound):
        await site.db.resolve_shortids([first], discarded=True)

    await site.cleanup_discarded()


async def test_query(site):
    await site.db.discard_datasets_by_dbids([10], True, '::')
    res = await site.db.bulk_tag([
        ('foo', 1),
        ('foo', 2),
    ], [], '::')

    res = await site.db.query()
    assert len(res) == 29

    res2 = await site.db.query(abbrev=True)
    assert [str(x)[0:10] for x in res] == [str(x) for x in res2]

    res = await site.db.query(collections=['hodge'])
    assert len(res) == 9

    res = await site.db.query(discarded=True)
    assert len(res) == 1

    res = await site.db.query(outdated=True)
    assert len(res) == 0

    res = await site.db.query(missing=True)
    assert len(res) == 0

    res = await site.db.query(path='/dev/null/')
    assert len(res) == 29

    res = await site.db.query(tags=['bar', 'baz'])
    assert len(res) == 0

    res = await site.db.query(tags=['bar', 'foo'])
    assert len(res) == 2
