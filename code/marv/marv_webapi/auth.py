# Copyright 2016 - 2021  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from json import JSONDecodeError

from aiohttp import web

from .api import api
from .tooling import generate_token


@api.endpoint('/auth', methods=['POST'], only_anon=True)
async def auth_post(request):
    try:
        req = await request.json()
        username = req['username']
        password = req['password']
    except (JSONDecodeError, KeyError):
        raise web.HTTPBadRequest

    if not username or not password:
        raise web.HTTPUnprocessableEntity

    if not await request.app['site'].db.authenticate(username, password):
        raise web.HTTPUnprocessableEntity

    return web.json_response({
        'access_token': generate_token(username, request.app['config']['SECRET_KEY']),
    })
