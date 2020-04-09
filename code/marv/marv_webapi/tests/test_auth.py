# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import time

import pytest


async def try_listing(client):
    return await client.get('/marv/api/collection', headers=client.headers)


async def try_details(client):
    return await client.get('/marv/api/dataset/aaaaaaaaaaaaaaaaaaaaaaaaqa', headers=client.headers)


async def try_filelist(client):
    return await client.post('/marv/api/file-list', headers=client.headers, json=[1])


async def try_comment(client):
    return await client.post('/marv/api/comment', headers=client.headers, json={
        '1': {'add': ['lorem ipsum', 'dolor']},
    })


async def try_delete(client):
    return await client.delete('/marv/api/dataset', headers=client.headers, json=[1])


async def try_tag(client):
    return await client.post('/marv/api/tag', headers=client.headers, json={
        'hodge': {'add': {f'tag{time.time()}': [1]}},
    })


@pytest.mark.marv(site={'acl': 'marv_webapi.acls:public'})
async def test_profile_public(client):  # pylint: disable=too-many-statements
    expected_acls = {
        'auth_post',
    }
    forbidden_acls = {
        'comment',
        'delete',
        'list',
        'read',
        'rpc_entry',
        'tag',
    }

    res = await client.get_json('/marv/api/meta')
    assert not expected_acls - set(res['acl'])
    assert not forbidden_acls & set(res['acl'])
    assert len(res['collections']) == 2
    res = await client.get_json('/marv/api/collection')
    assert res['acl'] == [
        'download_raw',
        'list',
        'read',
    ]
    res = await try_listing(client)
    assert res.status == 200
    res = await try_details(client)
    assert res.status == 200
    res = await try_filelist(client)
    assert res.status == 200
    res = await try_comment(client)
    assert res.status == 401
    res = await try_tag(client)
    assert res.status == 401
    res = await try_delete(client)
    assert res.status == 401

    await client.authenticate('test', 'test_pw')
    expected_acls = {
        'rpc_entry',
    }
    forbidden_acls = {
        'auth_post',
        'comment',
        'delete',
        'list',
        'read',
        'tag',
    }

    res = await client.get_json('/marv/api/meta')
    assert not expected_acls - set(res['acl'])
    assert not forbidden_acls & set(res['acl'])
    assert len(res['collections']) == 2
    res = await client.get_json('/marv/api/collection')
    assert res['acl'] == [
        'comment',
        'compare',
        'download_raw',
        'list',
        'read',
        'tag',
    ]
    res = await try_listing(client)
    assert res.status == 200
    res = await try_details(client)
    assert res.status == 200
    res = await try_filelist(client)
    assert res.status == 200
    res = await try_comment(client)
    assert res.status == 200
    res = await try_tag(client)
    assert res.status == 200
    res = await try_delete(client)
    assert res.status == 403

    await client.authenticate('adm', 'adm_pw')
    res = await client.get_json('/marv/api/meta')
    assert not expected_acls - set(res['acl'])
    assert not forbidden_acls & set(res['acl'])
    assert len(res['collections']) == 2
    res = await client.get_json('/marv/api/collection')
    assert res['acl'] == [
        'comment',
        'compare',
        'delete',
        'download_raw',
        'list',
        'read',
        'tag',
    ]
    res = await try_listing(client)
    assert res.status == 200
    res = await try_details(client)
    assert res.status == 200
    res = await try_filelist(client)
    assert res.status == 200
    res = await try_comment(client)
    assert res.status == 200
    res = await try_tag(client)
    assert res.status == 200
    res = await try_delete(client)
    assert res.status == 200


@pytest.mark.marv(site={'acl': 'marv_webapi.acls:authenticated'})
async def test_profile_authenticated(client):  # pylint: disable=too-many-statements
    expected_acls = {
        'auth_post',
    }
    forbidden_acls = {
        'comment',
        'delete',
        'list',
        'read',
        'rpc_entry',
        'tag',
    }

    res = await client.get_json('/marv/api/meta')
    assert len(res['collections']) == 0
    res = await try_listing(client)
    assert res.status == 401
    res = await try_details(client)
    assert res.status == 401
    res = await try_filelist(client)
    assert res.status == 401
    res = await try_comment(client)
    assert res.status == 401
    res = await try_tag(client)
    assert res.status == 401
    res = await try_delete(client)
    assert res.status == 401

    await client.authenticate('test', 'test_pw')
    expected_acls = {
        'rpc_entry',
    }
    forbidden_acls = {
        'auth_post',
        'comment',
        'delete',
        'list',
        'read',
        'tag',
    }

    res = await client.get_json('/marv/api/meta')
    assert not expected_acls - set(res['acl'])
    assert not forbidden_acls & set(res['acl'])
    assert len(res['collections']) == 2
    res = await client.get_json('/marv/api/collection')
    assert res['acl'] == [
        'comment',
        'compare',
        'download_raw',
        'list',
        'read',
        'tag',
    ]
    res = await try_listing(client)
    assert res.status == 200
    res = await try_details(client)
    assert res.status == 200
    res = await try_filelist(client)
    assert res.status == 200
    res = await try_comment(client)
    assert res.status == 200
    res = await try_tag(client)
    assert res.status == 200
    res = await try_delete(client)
    assert res.status == 403

    await client.authenticate('adm', 'adm_pw')
    res = await client.get_json('/marv/api/meta')
    assert not expected_acls - set(res['acl'])
    assert not forbidden_acls & set(res['acl'])
    assert len(res['collections']) == 2
    res = await client.get_json('/marv/api/collection')
    assert res['acl'] == [
        'comment',
        'compare',
        'delete',
        'download_raw',
        'list',
        'read',
        'tag',
    ]
    res = await try_listing(client)
    assert res.status == 200
    res = await try_details(client)
    assert res.status == 200
    res = await try_filelist(client)
    assert res.status == 200
    res = await try_comment(client)
    assert res.status == 200
    res = await try_tag(client)
    assert res.status == 200
    res = await try_delete(client)
    assert res.status == 200


async def test_authentication(client, site):
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
