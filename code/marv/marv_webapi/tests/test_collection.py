# Copyright 2016 - 2021  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import json


async def test_collection(app, site, client):
    await client.authenticate('test', 'test_pw')

    await site.db.bulk_tag([
        ('foo', 1),
        ('foo', 2),
    ], [], '::')

    res = await client.get_json('/marv/api/_collection/notexist')
    assert res.status == 403

    res = await client.get_json('/marv/api/_collection/hodge')
    assert len(res['listing']['widget']['data']['rows']) == 10

    res = await client.get_json('/marv/api/_collection/hodge', params={
        'filter': json.dumps({'not exist': {'val': 42, 'op': 'eq'}}),
    })
    assert res.status == 400

    res = await client.get_json('/marv/api/_collection/hodge', params={
        'filter': json.dumps({'f_name': {'val': 42, 'op': 'not exist'}}),
    })
    assert res.status == 400

    res = await client.get_json('/marv/api/_collection/hodge')
    app['debug'] = True
    res2 = await client.get_json('/marv/api/_collection/hodge')
    assert res == res2

    res = await client.get_json('/marv/api/_collection/hodge', params={
        'filter': json.dumps({'f_name': {'val': 'filtér', 'op': 'eq'}}),
    })
    assert 'listing' in res
