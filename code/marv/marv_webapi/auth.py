# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from aiohttp import web

from .tooling import api_group as marv_api_group, generate_token


@marv_api_group()
def auth(_):
    pass


@auth.endpoint('/auth', methods=['POST'], force_acl=['__unauthenticated__'])
async def auth_post(request):
    req = await request.json()
    if not req:
        raise web.HTTPBadRequest()
    username = req.get('username', '')
    password = req.get('password', '')

    if not await request.app['site'].db.authenticate(username, password):
        raise web.HTTPUnprocessableEntity()

    key = request.app['config']['SECRET_KEY']
    return web.json_response({'access_token': generate_token(username, key).decode('utf-8')})
