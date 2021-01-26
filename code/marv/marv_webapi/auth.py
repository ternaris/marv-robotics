# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from json import JSONDecodeError

from aiohttp import web

from .tooling import api_group as marv_api_group
from .tooling import generate_token


@marv_api_group()
def auth(_):
    pass


@auth.endpoint('/auth', methods=['POST'], force_acl=['__unauthenticated__'])
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
