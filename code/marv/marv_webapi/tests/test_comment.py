# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only


async def test_comment(client):
    await client.authenticate('test', 'test_pw')

    res = await client.post('/marv/api/comment', headers=client.headers, json={})
    assert res.status == 400

    res = await client.post_json('/marv/api/comment', json={
        '1': {
            'add': ['lorem ipsum', 'dolor'],
        },
    })
    assert res == {}
