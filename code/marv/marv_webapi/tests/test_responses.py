# Copyright 2016 - 2021  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from pathlib import Path

import pytest

from marv.tests.conftest import recorded
from marv.tests.test_dump_restore import postscan

DATADIR = Path(__file__).parent / 'data'


async def get_listings(client):
    metadata = await client.get_json('/marv/api/meta')
    listings = {}
    for colinfo in metadata['collections']:
        name = colinfo['name']
        listings[name] = await client.get_json(f'/marv/api/_collection/{name}')
    return listings


def get_rows(listing):
    rows = listing['listing']['widget']['data']['rows']
    lst = []
    for row in sorted(rows, key=lambda x: x['setid']):
        del row['id']
        lst.append(row)
    return lst


@pytest.mark.marv(site={'empty': True})
async def test_empty_responses(client, site):
    await site.db.user_add('test', password='test_pw', realm='marv', realmuid='')
    await client.authenticate('test', 'test_pw')
    assert recorded(await get_listings(client), DATADIR / 'empty_listings.json')


@pytest.mark.marv(site={'postscan': postscan, 'size': 2})
async def test_full_responses(client, site):
    await client.authenticate('test', 'test_pw')
    sets = await site.db.get_datasets_for_collections(None)
    for setid in sets:
        await site.run(setid)

    listings = await get_listings(client)
    listings = {k: get_rows(v) for k, v in listings.items()}
    assert recorded(listings, DATADIR / 'full_listings.json')

    details = []
    for colname, rows in sorted(listings.items()):
        for row in rows:
            detail = await client.get_json(f'/marv/api/dataset/{row["setid"]}')
            del detail['id']
            assert detail['collection'] == colname
            details.append(detail)
    assert recorded(details, DATADIR / 'full_details.json')
