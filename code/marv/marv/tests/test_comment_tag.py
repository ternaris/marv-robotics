# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only


async def test_comment(site):
    sets = await site.db.get_datasets_for_collections(None)

    # with setids
    await site.db.comment_multiple(sets[0:2], 'test', 'lorem ipsum')
    await site.db.comment_multiple(sets[0:1], 'test', 'dolor')

    res = await site.db.get_comments_for_setids(sets[0:1])
    assert len(res) == 2
    assert res[0].text == 'lorem ipsum'
    assert res[1].text == 'dolor'

    await site.db.comment_multiple(sets[0:1], 'test', 'sit amet')
    res = await site.db.get_comments_for_setids(sets[0:1])
    assert len(res) == 3
    assert res[2].text == 'sit amet'

    # bulkish
    await site.db.bulk_comment([
        {'dataset_id': 1, 'author': 'test', 'text': 'consectetur', 'time_added': 1},
        {'dataset_id': 1, 'author': 'test', 'text': 'adipiscing', 'time_added': 1},
    ])
    res = await site.db.get_comments_for_setids(sets[0:1])
    assert len(res) == 5
    assert res[3].text == 'consectetur'
    assert res[4].text == 'adipiscing'

    # get all
    res = await site.db.get_comments_for_setids([])
    assert len(res) == 6

    # delete
    res = await site.db.delete_comments_by_ids([1])
    res = await site.db.get_comments_for_setids([])
    assert len(res) == 5
    res = await site.db.get_comments_for_setids(sets[0:1])
    assert len(res) == 4

    await site.db.delete_comments_tags(sets[0:1], True, False)
    res = await site.db.get_comments_for_setids(sets[0:1])
    assert len(res) == 0


async def test_tag(site):
    sets = await site.db.get_datasets_for_collections(None)

    # add / remove
    await site.db.update_tags_for_setids(sets[0:1], add=['foo', 'bar'], remove=[])
    await site.db.update_tags_for_setids(sets[0:1], add=[], remove=['foo'])
    await site.db.update_tags_for_setids(sets[100:101], add=['baz'], remove=[])
    await site.db.update_tags_for_setids(sets[101:102], add=['baz', 'bar'], remove=[])

    # get all
    res = await site.db.get_all_known_tags_for_collection('hodge')
    assert res == ['bar', 'foo']
    res = await site.db.get_all_known_tags_for_collection('podge')
    assert res == ['bar', 'baz']

    # list
    res = await site.db.list_tags()
    assert res == ['bar', 'baz', 'foo']

    res = await site.db.list_tags(collections=['hodge'])
    assert res == ['bar', 'foo']

    # cleanup
    res = await site.db.cleanup_tags()
    res = await site.db.list_tags()
    assert res == ['bar', 'baz']

    # bulk
    res = await site.db.bulk_tag([
        ('hodge', 'foo', 1),
        ('hodge', 'foo', 2),
    ], [])
    res = await site.db.list_tags()
    assert res == ['bar', 'baz', 'foo']

    res = await site.db.bulk_tag([], [
        ('hodge', 'bar', 1),
    ])
    res = await site.db.cleanup_tags()
    res = await site.db.list_tags()
    assert res == ['bar', 'baz', 'foo']
    res = await site.db.list_tags(collections=['hodge'])
    assert res == ['foo']
    res = await site.db.list_tags(collections=['podge'])
    assert res == ['bar', 'baz']

    await site.db.delete_comments_tags([sets[x] for x in [0, 1, 100, 101]], False, True)
    res = await site.db.cleanup_tags()
    res = await site.db.list_tags()
    assert res == []
