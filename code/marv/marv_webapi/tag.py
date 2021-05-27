# Copyright 2016 - 2021  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from json import JSONDecodeError

from aiohttp import web

from marv.db import DBPermissionError

from .api import api
from .tooling import HTTPPermissionError


@api.endpoint('/tag', methods=['POST'])
async def tag(request):  # noqa: C901
    try:
        changes = await request.json()
    except JSONDecodeError:
        raise web.HTTPBadRequest

    if not changes:
        raise web.HTTPBadRequest

    try:
        add = []
        remove = []
        for ops in changes.values():
            for opname, target in (('add', add), ('remove', remove)):
                for tagname, ids in ops.pop(opname, {}).items():
                    for id in ids:
                        target.append((tagname, id))
            if ops:
                raise web.HTTPBadRequest
    except AttributeError:
        raise web.HTTPBadRequest

    try:
        await request.app['site'].db.bulk_tag(add, remove, user=request['username'])
    except DBPermissionError:
        raise HTTPPermissionError(request)
    return web.json_response({})
