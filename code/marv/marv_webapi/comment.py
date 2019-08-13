# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import time

from aiohttp import web

from marv.model import Comment, scoped_session
from .tooling import api_endpoint as marv_api_endpoint


@marv_api_endpoint('/comment', methods=['POST'])
async def comment(request):
    username = request['username']
    changes = await request.json()
    if not changes:
        raise web.HTTPBadRequest()

    with scoped_session(request.app['site']) as session:
        for id, ops in changes.items():
            now = int(time.time() * 1000)
            comments = [Comment(dataset_id=id, author=username, time_added=now, text=text)
                        for text in ops.get('add', [])]
            session.add_all(comments)

    # TODO: inform about unknown setids?

    return web.json_response({})
