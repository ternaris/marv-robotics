# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only


from marv_webapi.acls import authenticated, public


async def test_acls(client, app):
    expected_acls = {
        'auth_post',
        'collection',
        'detail',
        'file_list',
        'meta',
    }
    forbidden_acls = {
        'comment',
        'delete',
        'rpc_entry',
        'tag',
    }

    app['acl'] = public()
    res = await client.get_json('/marv/api/meta')
    assert not expected_acls - set(res['acl'])
    assert not forbidden_acls & set(res['acl'])

    app['acl'] = authenticated()
    res = await client.get_json('/marv/api/meta')
    assert res == {'realms': []}

    await client.authenticate('test', 'test_pw')
    expected_acls = {
        'collection',
        'comment',
        'detail',
        'file_list',
        'meta',
        'rpc_entry',
        'tag',
    }
    forbidden_acls = {
        'auth_post',
        'delete',
    }

    app['acl'] = public()
    res = await client.get_json('/marv/api/meta')
    assert not expected_acls - set(res['acl'])
    assert not forbidden_acls & set(res['acl'])

    app['acl'] = authenticated()
    res = await client.get_json('/marv/api/meta')
    assert not expected_acls - set(res['acl'])
    assert not forbidden_acls & set(res['acl'])

    await client.authenticate('adm', 'adm_pw')
    expected_acls = {
        'collection',
        'comment',
        'delete',
        'detail',
        'file_list',
        'meta',
        'rpc_entry',
        'tag',
    }
    forbidden_acls = {
        'auth_post',
    }

    app['acl'] = public()
    res = await client.get_json('/marv/api/meta')
    assert not expected_acls - set(res['acl'])
    assert not forbidden_acls & set(res['acl'])

    app['acl'] = authenticated()
    res = await client.get_json('/marv/api/meta')
    assert not expected_acls - set(res['acl'])
    assert not forbidden_acls & set(res['acl'])


async def test_auth(client, site):
    res = await client.post('/marv/api/auth', json={})
    assert res.status == 400

    res = await client.post('/marv/api/auth', json={'username': 'foo', 'password': 'bar'})
    assert res.status == 422

    res = await client.post_json('/marv/api/auth', json={'username': 'test', 'password': 'test_pw'})
    assert res['access_token']

    await client.authenticate('test', 'test_pw')
    await site.db.user_rm('test')
    res = await client.get('/marv/api/meta', headers=client.headers)
    assert res.status == 401

    client.headers['Authorization'] = 'Basic XXXX'
    res = await client.get('/marv/api/meta', headers=client.headers)
    assert res.status == 401
