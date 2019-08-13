# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from aiohttp import web

from marv.model import Dataset, scoped_session
from .tooling import api_endpoint as marv_api_endpoint


@marv_api_endpoint('/dataset', methods=['DELETE'])
async def delete(request):
    datasets = Dataset.__table__
    ids = await request.json()
    if not ids:
        raise web.HTTPBadRequest()
    stmt = datasets.update()\
                   .where(datasets.c.id.in_(ids))\
                   .values(discarded=True)
    with scoped_session(request.app['site']) as session:
        session.execute(stmt)
    return web.json_response({})
