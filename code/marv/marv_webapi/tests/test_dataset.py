# Copyright 2016 - 2021  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path


async def test_dataset(site, client):
    await client.authenticate('test', 'test_pw')

    sets = await site.db.get_datasets_for_collections(None)

    res = await client.get_json('/marv/api/dataset/xxxxxxxxxxxxxxxxxxxxxxxxxx', json={})
    assert res.status == 403

    res = await client.get_json(f'/marv/api/dataset/{sets[0]}')
    assert res['title'] == 'hodge_0001'

    # 404 with virtual scanroot
    res = await client.get_json(f'/marv/api/dataset/{sets[0]}/0')
    assert res.status == 404

    # 403 for absolute file
    res = await client.get_json(f'/marv/api/dataset/{sets[0]}//absolute')
    assert res.status == 403

    # filelist
    res = await client.post_json('/marv/api/file-list', json=[])
    assert res.status == 400

    res = await client.post_json('/marv/api/file-list', json=[1, 2])
    assert [x.split('/')[-1] for x in res['paths']] == ['0001', '0002']
    assert [x.split('/')[-1] for x in res['urls']] == ['0', '0']


async def test_nginx(site, client, mocker):
    site.config = site.config.copy(update={
        'marv': site.config.marv.copy(update={'reverse_proxy': 'nginx'}),
    })

    sets = await site.db.get_datasets_for_collections(None)

    await client.authenticate('test', 'test_pw')

    async def get_filepath(*args):  # pylint: disable=unused-argument
        return Path('/dev/null/foo')

    mocker.patch('marv_webapi.dataset._get_filepath', wraps=get_filepath)

    res = await client.get_json(f'/marv/api/dataset/{sets[0]}/0')
    assert res.status == 200
    assert res.headers['x-accel-redirect'] == '/dev/null/foo'
