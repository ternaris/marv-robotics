# Copyright 2016 - 2021  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import time

from aiohttp import web

from marv.db import DBPermissionError

from .api import api
from .tooling import HTTPPermissionError


@api.endpoint('/comment', methods=['POST'])
async def comment(request):
    username = request['username']
    changes = await request.json()
    if not changes:
        raise web.HTTPBadRequest()

    now = int(time.time() * 1000)
    comments = [
        {'dataset_id': id, 'author': username, 'time_added': now, 'text': text}
        for id, ops in changes.items()
        for text in ops.get('add', [])
    ]
    try:
        await request.app['site'].db.bulk_comment(comments, user=username)
    except DBPermissionError:
        raise HTTPPermissionError(request)

    return web.json_response({})
