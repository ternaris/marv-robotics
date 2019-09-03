# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import json

import pytest

from marv.db import UnknownOperator


async def test_listing(site):
    # pylint: disable=too-many-statements

    sets = await site.db.get_datasets_for_collections(['hodge'])
    for setid in sets:
        await site.run(setid)

    await site.db.comment_multiple([sets[2]], 'test', 'lorem ipsum')

    res = await site.db.bulk_tag([
        ('hodge', 'foo', 1),
        ('hodge', 'foo', 2),
        ('hodge', 'bar', 1),
    ], [])

    collection = site.collections['hodge']
    descs = collection.table_descriptors

    res = await site.db.get_all_known_for_collection(collection)
    assert res == {
        'divisors': [f'div{x}' for x in range(1, 51)],
        'node_test': [str(x) for x in range(1, 51)],
        'status': ['error', 'missing', 'outdated', 'pending'],
        'tags': ['bar', 'foo'],
    }

    res = await site.db.get_filtered_listing(descs, [])
    assert len(res) == 50

    # by comment
    res = await site.db.get_filtered_listing(descs, [
        ('comments', 'rem', 'substring', 'string'),
    ])
    assert len(res) == 1
    assert res[0]['id'] == 3

    # by tag
    res = await site.db.get_filtered_listing(descs, [
        ('tags', ['bar', 'foo'], 'any', 'string'),
    ])
    assert len(res) == 2
    assert res[0]['id'] == 1
    assert res[1]['id'] == 2

    res = await site.db.get_filtered_listing(descs, [
        ('tags', ['bar', 'foo'], 'all', 'string'),
    ])
    assert len(res) == 1
    assert res[0]['id'] == 1

    with pytest.raises(UnknownOperator):
        res = await site.db.get_filtered_listing(descs, [
            ('tags', ['bar', 'foo'], 'bad operator', 'string'),
        ])

    # TODO: status

    # datetime
    day1 = 1400000000000 + 24 * 3600 * 1000
    day2 = day1 + 24 * 3600 * 1000
    res = await site.db.get_filtered_listing(descs, [
        ('time_added', day1, 'eq', 'datetime'),
    ])
    assert len(res) == 2
    times = [json.loads(x['row'])['values'][4] for x in res]
    assert all(day1 <= x < day2 for x in times)

    res = await site.db.get_filtered_listing(descs, [
        ('time_added', day1, 'ne', 'datetime'),
    ])
    assert len(res) == 48
    times = [json.loads(x['row'])['values'][4] for x in res]
    assert all(x < day1 or x >= day2 for x in times)

    res = await site.db.get_filtered_listing(descs, [
        ('time_added', day1, 'lt', 'datetime'),
    ])
    assert len(res) == 2
    times = [json.loads(x['row'])['values'][4] for x in res]
    assert all(x < day1 for x in times)

    res = await site.db.get_filtered_listing(descs, [
        ('time_added', day1, 'le', 'datetime'),
    ])
    assert len(res) == 4
    times = [json.loads(x['row'])['values'][4] for x in res]
    assert all(x < day2 for x in times)

    res = await site.db.get_filtered_listing(descs, [
        ('time_added', day1, 'gt', 'datetime'),
    ])
    assert len(res) == 46
    times = [json.loads(x['row'])['values'][4] for x in res]
    assert all(x > day1 for x in times)

    res = await site.db.get_filtered_listing(descs, [
        ('time_added', day1, 'ge', 'datetime'),
    ])
    assert len(res) == 48
    times = [json.loads(x['row'])['values'][4] for x in res]
    assert all(x >= day1 for x in times)

    # substring
    res = await site.db.get_filtered_listing(descs, [
        ('setid', '43', 'substring', 'string'),
    ])
    assert len(res) == 2
    assert res[0]['id'] == 25
    assert res[1]['id'] == 1

    # startswith
    res = await site.db.get_filtered_listing(descs, [
        ('setid', 'tv43', 'startswith', 'string'),
    ])
    assert len(res) == 1
    assert res[0]['id'] == 1

    # lt
    res = await site.db.get_filtered_listing(descs, [('size', 10, 'lt', 'int')])
    assert len(res) == 9

    # le
    res = await site.db.get_filtered_listing(descs, [('size', 10, 'le', 'int')])
    assert len(res) == 10

    # eq
    res = await site.db.get_filtered_listing(descs, [('size', 10, 'eq', 'int')])
    assert len(res) == 1

    # ge
    res = await site.db.get_filtered_listing(descs, [('size', 10, 'ge', 'int')])
    assert len(res) == 41

    # gt
    res = await site.db.get_filtered_listing(descs, [('size', 10, 'gt', 'int')])
    assert len(res) == 40

    # ne
    res = await site.db.get_filtered_listing(descs, [('size', 10, 'ne', 'int')])
    assert len(res) == 49

    # relations
    res = await site.db.get_filtered_listing(descs, [
        ('divisors', ['div17'], 'any', 'string'),
    ])
    assert [x['id'] for x in res] == [17, 34]

    res = await site.db.get_filtered_listing(descs, [
        ('divisors', ['div2', 'div17'], 'all', 'string'),
    ])
    assert [x['id'] for x in res] == [34]

    res = await site.db.get_filtered_listing(descs, [
        ('divisors', 'iv4', 'substring_any', 'string'),
    ])
    assert [x['id'] for x in res] == list(range(4, 41, 4)) + list(range(41, 50))

    # TODO: words

# TODO: add test for cleanup_listing_relations
