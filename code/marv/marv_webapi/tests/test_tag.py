# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only


async def test_tag(client, site):
    await client.authenticate('test', 'test_pw')

    res = await client.post('/marv/api/tag', headers=client.headers, json={})
    assert res.status == 400

    res = await client.post('/marv/api/tag', headers=client.headers, json={
        'notexist': {
            'add': {
                'important': [1, 2, 3],
            },
        },
    })
    assert res.status == 400

    res = await client.post_json('/marv/api/tag', json={
        'hodge': {
            'add': {
                'important': [1, 2, 3],
            },
        },
    })
    assert res == {}

    res = await site.db.get_setids(await site.db.query(tags=['important']), dbids=True)
    assert sorted(res) == [1, 2, 3]
