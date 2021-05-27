# Copyright 2016 - 2021  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from json import JSONDecodeError

from aiohttp import web

from marv.db import DBPermissionError

from .api import api
from .tooling import HTTPPermissionError


@api.endpoint('/dataset', methods=['DELETE'])
async def delete(request):
    try:
        ids = await request.json()
    except JSONDecodeError:
        raise web.HTTPBadRequest

    if not ids:
        raise web.HTTPBadRequest

    try:
        await request.app['site'].db.discard_datasets_by_dbids(ids, True, user=request['username'])
    except DBPermissionError:
        raise HTTPPermissionError(request)

    return web.json_response({})
