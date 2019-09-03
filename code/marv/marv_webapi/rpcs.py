# Copyright 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import json
from collections import defaultdict

from aiohttp import web
from tortoise.exceptions import OperationalError

from .tooling import api_group as marv_api_group


@marv_api_group()
def rpcs(_):
    pass


@rpcs.endpoint('/v1/rpcs', methods=['POST'], force_acl=['__authenticated__'])  # noqa: C901
async def rpc_entry(request):
    # pylint: disable=too-many-locals

    try:
        posted = await request.json()
    except json.JSONDecodeError as err:
        raise web.HTTPBadRequest(text=json.dumps({'errors': ['request is not JSON']}))
    if not posted:
        raise web.HTTPBadRequest(text=json.dumps({'errors': ['nothing posted']}))
    if 'rpcs' not in posted:
        raise web.HTTPBadRequest(text=json.dumps({'errors': ['no rpcs posted']}))

    res = {'data': defaultdict(list)}

    for rpc in posted['rpcs']:
        calls = list(rpc.items())
        if len(calls) != 1:
            raise web.HTTPBadRequest(text=json.dumps({
                'errors': ['rpc should be a single key value pair'],
            }))

        func, payload = calls[0]
        if func == 'query':
            model = payload.get('model')
            filters = payload.get('filters', {})
            attrs = payload.get('attrs', {})
            order = payload.get('order')
            limit = payload.get('limit')
            offset = payload.get('offset')
            try:
                result = await request.app['site'].db.rpc_query(model, filters, attrs,
                                                                order, limit, offset)
            except (OperationalError, ValueError) as err:
                raise web.HTTPBadRequest(text=json.dumps({'errors': [str(err)]}))

            aliases = payload.get('aliases', {})
            for key, values in result.items():
                res['data'][aliases.get(key, key)].extend(values)
        else:
            raise web.HTTPBadRequest(text=f'unknown rpc function "{func}"')

    return web.json_response(res)
