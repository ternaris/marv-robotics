# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from aiohttp import web

from marv.db import DBPermissionError
from .tooling import HTTPPermissionError, api_endpoint as marv_api_endpoint


@marv_api_endpoint('/tag', methods=['POST'])
async def tag(request):
    changes = await request.json()
    if not changes:
        raise web.HTTPBadRequest()

    add = []
    remove = []
    for collection, ops in changes.items():
        if collection not in request.app['site'].collections:
            raise web.HTTPBadRequest()

        for opname, target in (('add', add), ('remove', remove)):
            for tagname, ids in ops.get(opname, {}).items():
                for id in ids:
                    target.append((tagname, id))

    try:
        await request.app['site'].db.bulk_tag(add, remove, user=request['username'])
    except DBPermissionError:
        raise HTTPPermissionError(request)
    return web.json_response({})
