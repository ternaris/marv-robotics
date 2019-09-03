# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only


async def test_dataset(site, client):
    await client.authenticate('adm', 'adm_pw')

    sets = await site.db.get_datasets_for_collections(None)

    res = await client.delete('/marv/api/dataset', headers=client.headers, json=[])
    assert res.status == 400

    res = await client.delete('/marv/api/dataset', headers=client.headers, json=[1])
    assert res.status == 200

    rest = await site.db.get_datasets_for_collections(None)
    assert set(sets) - set(rest) == {sets[0]}

    await client.authenticate('test', 'test_pw')
    res = await client.delete('/marv/api/dataset', headers=client.headers, json=[2])
    assert res.status == 403
