# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from aiohttp import web

from marv.db import DBPermissionError
from .tooling import HTTPPermissionError, api_endpoint as marv_api_endpoint


@marv_api_endpoint('/dataset', methods=['DELETE'])
async def delete(request):
    ids = await request.json()
    if not ids:
        raise web.HTTPBadRequest()
    try:
        await request.app['site'].db.discard_datasets_by_dbids(ids, user=request['username'])
    except DBPermissionError:
        raise HTTPPermissionError(request)
    return web.json_response({})
