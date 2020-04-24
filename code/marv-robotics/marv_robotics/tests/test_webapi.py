# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only


async def test_docs(client):
    res = await client.get('/docs/')
    assert res.status == 200

    res = await client.get('/docs//absolute')
    assert res.status == 403
