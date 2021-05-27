# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import pytest


@pytest.mark.marv(site={'size': 50})
async def test_rpc_query(site, client):
    # pylint: disable=too-many-statements

    sets = await site.db.get_datasets_for_collections(None)
    for setid in sets:
        await site.run(setid)

    res = await client.post('/marv/api/v1/rpcs', json={'rpcs': []})
    assert res.status == 401

    await client.authenticate('test', 'test_pw')

    # empty query
    res = await client.post_json('/marv/api/v1/rpcs', json={'rpcs': []})
    assert res == {'data': {}}

    # most basic query
    res = await client.post_json('/marv/api/v1/rpcs', json={'rpcs': [{'query': {
        'model': 'dataset',
    }}]})
    assert 'dataset' in res['data']
    assert len(res['data']['dataset']) == 150
    assert res['data']['dataset'][0] == {
        'collection': 'hodge',
        'discarded': 0,
        'id': 1,
        'name': 'hodge_0001',
        'setid': 'aaaaaaaaaaaaaaaaaaaaaaaaqa',
        'status': 0,
        'time_added': 1400000000000,
        'timestamp': 1500001000000,
    }

    # query with filtered attrs
    res = await client.post_json('/marv/api/v1/rpcs', json={'rpcs': [{'query': {
        'model': 'dataset',
        'attrs': {
            'name': True,
        },
    }}]})
    assert res['data']['dataset'][0] == {'id': 1, 'name': 'hodge_0001'}

    # query filters
    def make_query(**query):
        query.setdefault('model', 'dataset')
        query.setdefault('attrs', {
            'collection': True,
            'name': True,
        })
        return {'rpcs': [{'query': query}]}

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'eq', 'name': 'id', 'value': 2},
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'hodge', 'id': 2, 'name': 'hodge_0002'},
        ],
    }

    # check non ascii values
    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'eq', 'name': 'name', 'value': 'filtér'},
    ]))
    assert res['data'] == {'dataset': []}

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'substring', 'name': 'name', 'value': 'filtér'},
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'hodge', 'id': 43, 'name': 'hodge_0043_filtér'},
            {'collection': 'podge', 'id': 93, 'name': 'podge_0043_filtér'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'substring', 'name': 'name', 'value': 'filt\xe9r'},
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'hodge', 'id': 43, 'name': 'hodge_0043_filtér'},
            {'collection': 'podge', 'id': 93, 'name': 'podge_0043_filtér'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'lte', 'name': 'id', 'value': 2},
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'hodge', 'id': 1, 'name': 'hodge_0001'},
            {'collection': 'hodge', 'id': 2, 'name': 'hodge_0002'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'lt', 'name': 'id', 'value': 2},
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'hodge', 'id': 1, 'name': 'hodge_0001'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'gte', 'name': 'id', 'value': 149},
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'podge', 'id': 149, 'name': 'podge_0099'},
            {'collection': 'podge', 'id': 150, 'name': 'podge_0100'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'gt', 'name': 'id', 'value': 149},
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'podge', 'id': 150, 'name': 'podge_0100'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'between', 'name': 'id', 'value': [2, 4]},
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'hodge', 'id': 2, 'name': 'hodge_0002'},
            {'collection': 'hodge', 'id': 3, 'name': 'hodge_0003'},
            {'collection': 'hodge', 'id': 4, 'name': 'hodge_0004'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'notbetween', 'name': 'id', 'value': [2, 149]},
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'hodge', 'id': 1, 'name': 'hodge_0001'},
            {'collection': 'podge', 'id': 150, 'name': 'podge_0100'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'in', 'name': 'id', 'value': [2, 4]},
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'hodge', 'id': 2, 'name': 'hodge_0002'},
            {'collection': 'hodge', 'id': 4, 'name': 'hodge_0004'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'between', 'name': 'id', 'value': [2, 4]},
        {'op': 'ne', 'name': 'name', 'value': 'hodge_0003'},
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'hodge', 'id': 2, 'name': 'hodge_0002'},
            {'collection': 'hodge', 'id': 4, 'name': 'hodge_0004'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'between', 'name': 'id', 'value': [2, 5]},
        {'op': 'notin', 'name': 'name', 'value': ['hodge_0003', 'hodge_0005']},
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'hodge', 'id': 2, 'name': 'hodge_0002'},
            {'collection': 'hodge', 'id': 4, 'name': 'hodge_0004'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'startswith', 'name': 'name', 'value': 'podge_01'},
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'podge', 'id': 150, 'name': 'podge_0100'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'startswith', 'name': 'name', 'value': '_'},
    ]))
    assert res['data'] == {'dataset': []}

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'endswith', 'name': 'name', 'value': '_0001'},
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'hodge', 'id': 1, 'name': 'hodge_0001'},
            {'collection': 'podge', 'id': 51, 'name': 'podge_0001'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'endswith', 'name': 'name', 'value': '_'},
    ]))
    assert res['data'] == {'dataset': []}

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'substring', 'name': 'name', 'value': '_'},
    ]))
    assert len(res['data']['dataset']) == 150

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'substring', 'name': 'name', 'value': '_01'},
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'podge', 'id': 150, 'name': 'podge_0100'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'like', 'name': 'name', 'value': 'hodge'},
    ]))
    assert not res['data']['dataset']

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'like', 'name': 'name', 'value': 'hodge%'},
    ]))
    assert len(res['data']['dataset']) == 50

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'notlike', 'name': 'name', 'value': 'hodge%'},
    ]))
    assert len(res['data']['dataset']) == 100

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'isnot', 'name': 'name', 'value': None},
    ]))
    assert len(res['data']['dataset']) == 150

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'is', 'name': 'name', 'value': None},
    ]))
    assert not res['data']['dataset']

    # explict boolean logic
    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'not', 'value': {'op': 'eq', 'name': 'id', 'value': 2}},
    ]))
    assert len(res['data']['dataset']) == 149
    assert 2 not in [x['id'] for x in res['data']['dataset']]

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {
            'op': 'and',
            'value': [
                {'op': 'gt', 'name': 'id', 'value': 2},
                {'op': 'lt', 'name': 'id', 'value': 5},
            ],
        },
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'hodge', 'id': 3, 'name': 'hodge_0003'},
            {'collection': 'hodge', 'id': 4, 'name': 'hodge_0004'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {
            'op': 'or',
            'value': [
                {'op': 'eq', 'name': 'id', 'value': 2},
                {'op': 'eq', 'name': 'name', 'value': 'podge_0001'},
            ],
        },
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'hodge', 'id': 2, 'name': 'hodge_0002'},
            {'collection': 'podge', 'id': 51, 'name': 'podge_0001'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'endswith', 'name': 'files.path', 'value': '0042'},
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'hodge', 'id': 42, 'name': 'hodge_0042'},
            {'collection': 'podge', 'id': 92, 'name': 'podge_0042'},
        ],
    }

    res = await site.db.bulk_tag((
        ('important', 2),
        ('important', 3),
        ('important', 150),
        ('check', 2),
    ), (), '::')

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(filters=[
        {'op': 'eq', 'name': 'tags.value', 'value': 'important'},
    ]))
    assert res['data'] == {
        'dataset': [
            {'collection': 'hodge', 'id': 2, 'name': 'hodge_0002'},
            {'collection': 'hodge', 'id': 3, 'name': 'hodge_0003'},
            {'collection': 'podge', 'id': 150, 'name': 'podge_0100'},
        ],
    }

    # relation embedding
    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(
        filters=[{'op': 'eq', 'name': 'tags.value', 'value': 'important'}],
        attrs={
            'name': True,
            'tags': {'value': True},
        },
    ))
    assert res['data'] == {
        'dataset': [
            {'id': 2, 'name': 'hodge_0002', 'tags': [1, 2]},
            {'id': 3, 'name': 'hodge_0003', 'tags': [2]},
            {'id': 150, 'name': 'podge_0100', 'tags': [2]},
        ],
        'tag': [
            {'id': 1, 'value': 'check'},
            {'id': 2, 'value': 'important'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(
        filters=[{'op': 'eq', 'name': 'tags.value', 'value': 'important'}],
        attrs={
            'name': True,
            'files': True,
        },
    ))
    assert res['data']['dataset'] == [
        {'id': 2, 'name': 'hodge_0002', 'files': [2]},
        {'id': 3, 'name': 'hodge_0003', 'files': [3]},
        {'id': 150, 'name': 'podge_0100', 'files': [150]},
    ]
    assert len(res['data']['file']) == 3
    assert len(list(res['data']['file'][0].keys())) == 7

    # order, limit, offset
    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(
        attrs={
            'name': True,
        },
        order=['name', 'ASC'],
        limit=3,
        offset=3,
    ))
    assert res['data'] == {
        'dataset': [
            {'id': 4, 'name': 'hodge_0004'},
            {'id': 5, 'name': 'hodge_0005'},
            {'id': 6, 'name': 'hodge_0006'},
        ],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json=make_query(
        attrs={
            'name': True,
        },
        order=['name', 'DESC'],
        limit=3,
        offset=3,
    ))
    assert res['data'] == {
        'dataset': [
            {'id': 147, 'name': 'podge_0097'},
            {'id': 146, 'name': 'podge_0096'},
            {'id': 145, 'name': 'podge_0095'},
        ],
    }

    # check users do not return password
    res = await client.post_json('/marv/api/v1/rpcs', json={'rpcs': [{'query': {
        'model': 'user',
    }}]})
    assert 'user' in res['data']
    assert len(res['data']['user']) == 2
    for user in res['data']['user']:
        assert 'password' not in user

    res = await client.post_json('/marv/api/v1/rpcs', json={'rpcs': [{'query': {
        'model': 'group',
        'attrs': {
            'users': True,
        },
    }}]})
    assert 'user' in res['data']
    assert [x['name'] for x in res['data']['user']] == ['adm']
    for user in res['data']['user']:
        assert 'password' not in user

    # internal users/groups are not returned
    res = await client.post_json('/marv/api/v1/rpcs', json={'rpcs': [{'query': {
        'model': 'user',
        'attrs': {
            'name': True,
            'groups': True,
        },
    }}]})
    assert res['data'] == {
        'group': [{'id': 3, 'name': 'admin'}],
        'user': [
            {'groups': [3], 'id': 3, 'name': 'adm'},
            {'groups': [], 'id': 2, 'name': 'test'},
        ],
    }

    # unknown fieldnames return bad request
    res = await client.post_json('/marv/api/v1/rpcs', json={'rpcs': [{'query': {
        'model': 'dataset',
        'attrs': {
            'invalid attr name': True,
        },
    }}]})
    assert res.status == 400
    assert "'invalid attr name'" in await res.text()

    res = await client.post_json('/marv/api/v1/rpcs', json={'rpcs': [{'query': {
        'model': 'dataset',
        'filters': [
            {'op': 'eq', 'name': 'invalid attr name', 'value': 1},
        ],
    }}]})
    assert res.status == 400
    assert "'invalid attr name'" in await res.text()

    # check virtual collection: models
    res = await client.post_json('/marv/api/v1/rpcs', json={'rpcs': [{'query': {
        'model': 'collection:hodge',
        'filters': [
            {'op': 'endswith', 'name': 'dataset.files.path', 'value': '/0001'},
        ],
        'attrs': {
            'dataset.files': True,
        },
    }}]})
    assert res['data'] == {
        'collection:hodge': [{'dataset.files': [1],
                              'id': 1,
                              'f_name': 'hodge_0001',
                              'f_setid': 'aaaaaaaaaaaaaaaaaaaaaaaaqa',
                              'f_size': 1,
                              'f_time_added': 1400000000000,
                              'f_time_mtime': 1500001000000}],
        'dataset.files': [{'dataset_id': 1,
                           'id': 1,
                           'idx': 0,
                           'missing': 0,
                           'mtime': 1500001000000,
                           'path': '/dev/null/hodge/0001',
                           'size': 1}],
    }

    res = await client.post_json('/marv/api/v1/rpcs', json={'rpcs': [{'query': {
        'model': 'collection:hodge',
        'filters': [
            {'op': 'endswith', 'name': 'dataset.files.path', 'value': '/0001'},
        ],
        'attrs': {
            'f_divisors': True,
        },
    }}]})
    assert res['data'] == {
        'collection:hodge': [{'f_divisors': [1],
                              'id': 1,
                              'f_name': 'hodge_0001',
                              'f_setid': 'aaaaaaaaaaaaaaaaaaaaaaaaqa',
                              'f_size': 1,
                              'f_time_added': 1400000000000,
                              'f_time_mtime': 1500001000000}],
        'f_divisors': [{'id': 1, 'value': 'div1'}],
    }
