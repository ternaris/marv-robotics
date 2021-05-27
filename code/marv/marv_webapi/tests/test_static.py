# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only


async def test_frontend(client):
    res = await client.get('/')
    assert res.status == 200
    assert res.headers['Content-Type'] == 'text/html; charset=utf-8'

    res = await client.get('/main-built.js')
    assert res.status == 200
    assert res.headers['Content-Type'] == 'application/javascript'
    data = await res.text(encoding='utf-8')
    assert data.startswith('/*')

    res = await client.get('/main-built.css')
    assert res.status == 200
    assert res.headers['Content-Type'] == 'text/css'
    data = await res.text(encoding='utf-8')
    assert data.startswith('/*')

    res = await client.get('/custom/not-exist.js')
    assert res.status == 404

    res = await client.get('/custom//absolute')
    assert res.status == 403

    res = await client.get('/custom/relative//withdoubleslash')
    assert res.status == 404

    res = await client.get('/not-exist.js')
    assert res.status == 404

    res = await client.get('somedir//absolute')
    assert res.status == 404

    # deactivate url validation in test framework,
    client.server.skip_url_asserts = True
    res = await client.get('////absolute')
    assert res.status == 403
