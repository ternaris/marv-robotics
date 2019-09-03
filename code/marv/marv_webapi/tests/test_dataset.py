# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only


async def test_dataset(site, client):
    await client.authenticate('test', 'test_pw')

    sets = await site.db.get_datasets_for_collections(None)

    res = await client.get('/marv/api/dataset/xxxxxxxxxxxxxxxxxxxxxxxxxx',
                           headers=client.headers, json={})
    assert res.status == 404

    res = await client.get_json(f'/marv/api/dataset/{sets[0]}')
    assert res['title'] == 'hodge_0001'

    # 404 with virtual scanroot
    res = await client.get(f'/marv/api/dataset/{sets[0]}/0')
    assert res.status == 404

    # filelist
    res = await client.post('/marv/api/file-list', headers=client.headers, json=[])
    assert res.status == 400

    res = await client.post_json('/marv/api/file-list', json=[1, 2])
    assert [x.split('/')[-1] for x in res['paths']] == ['0001', '0002']
    assert [x.split('/')[-1] for x in res['urls']] == ['0', '0']
