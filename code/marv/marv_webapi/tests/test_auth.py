# Copyright 2016 - 2021  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import time
from collections import namedtuple

import pytest


async def try_listing(client):
    return await client.get('/marv/api/_collection', headers=client.headers)


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


async def try_untag(client):
    tag = f'tag{time.time()}'

    auth = await client.unauthenticate()
    await client.authenticate('adm', 'adm_pw')
    await client.post('/marv/api/tag', headers=client.headers, json={
        'hodge': {'add': {tag: [1]}},
    })
    await client.unauthenticate()
    if auth:
        client.headers['Authorization'] = auth

    return await client.post('/marv/api/tag', headers=client.headers, json={
        'hodge': {'remove': {tag: [1]}},
    })


class AuthtestParams(namedtuple('Param', 'count expected forbidden local calls')):
    def __new__(cls, *args):
        assert len(args[-1]) == 7
        return super().__new__(cls, *args)


UNAUTH_PUBLIC = AuthtestParams(
    2,
    set(),
    {'admin'},
    {'download_raw', 'list', 'read'},
    [(200, try_listing),
     (200, try_details),
     (200, try_filelist),
     (401, try_comment),
     (401, try_tag),
     (401, try_untag),
     (401, try_delete)],
)

UNAUTH_AUTHENTICATED = AuthtestParams(
    0,
    set(),
    {'admin'},
    set(),
    [(401, try_listing),
     (401, try_details),
     (401, try_filelist),
     (401, try_comment),
     (401, try_tag),
     (401, try_untag),
     (401, try_delete)],
)

AUTH = AuthtestParams(
    2,
    set(),
    {'admin'},
    {'download_raw', 'list', 'read', 'comment', 'tag'},
    [(200, try_listing),
     (200, try_details),
     (200, try_filelist),
     (200, try_comment),
     (200, try_tag),
     (200, try_untag),
     (403, try_delete)],
)

ADMIN = AuthtestParams(
    2,
    {'admin'},
    set(),
    {'download_raw', 'list', 'read', 'comment', 'tag', 'delete'},
    [(200, try_listing),
     (200, try_details),
     (200, try_filelist),
     (200, try_comment),
     (200, try_tag),
     (200, try_untag),
     (200, try_delete)],
)


@pytest.mark.parametrize('auth, params', [
    pytest.param(
       None, UNAUTH_PUBLIC,
       marks=pytest.mark.marv(site={'acl': 'marv_webapi.acls:public'}),
    ),
    pytest.param(
       ('test', 'test_pw'), AUTH,
       marks=pytest.mark.marv(site={'acl': 'marv_webapi.acls:public'}),
    ),
    pytest.param(
       ('adm', 'adm_pw'), ADMIN,
       marks=pytest.mark.marv(site={'acl': 'marv_webapi.acls:public'}),
    ),
    pytest.param(
        None, UNAUTH_AUTHENTICATED,
        marks=pytest.mark.marv(site={'acl': 'marv_webapi.acls:authenticated'}),
    ),
    pytest.param(
        ('test', 'test_pw'), AUTH,
        marks=pytest.mark.marv(site={'acl': 'marv_webapi.acls:authenticated'}),
    ),
    pytest.param(
        ('adm', 'adm_pw'), ADMIN,
        marks=pytest.mark.marv(site={'acl': 'marv_webapi.acls:authenticated'}),
    ),
])
async def test_profiles(client, auth, params):
    if auth:
        await client.authenticate(*auth)

    # check global permissions (non action routes) on meta
    res = await client.get_json('/marv/api/meta')
    assert not params.expected - set(res['acl'])
    assert not params.forbidden & set(res['acl'])
    assert len(res['collections']) == params.count

    # check local permissions on collection
    res = await client.get_json('/marv/api/_collection')
    if params.local:
        assert set(res['acl']) == params.local
    else:
        assert res.status == 401

    # try accessing actions
    for code, func in params.calls:
        assert (await func(client)).status == code


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
