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
async def rpc_entry(request):  # noqa: C901
    # pylint: disable=too-many-locals,too-many-branches

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
            # v1 keeps collection
            if 'collection' in attrs:
                attrs['collection_id'] = attrs.pop('collection')
            # /v1 keeps collection
            try:
                result = await request.app['site'].db.rpc_query(model, filters, attrs,
                                                                order, limit, offset)
            except (OperationalError, ValueError) as err:
                raise web.HTTPBadRequest(text=json.dumps({'errors': [str(err)]}))

            aliases = payload.get('aliases', {})
            for key, values in result.items():
                # v1 keeps collection
                if key == 'dataset':
                    try:
                        collections = {
                            x['id']: x['name']
                            for x in (
                                await request.app['site'].db.rpc_query('collection', {}, {},
                                                                       None, None, None)
                            )['collection']
                        }
                        for value in values:
                            if 'collection_id' in value:
                                value['collection'] = collections[value.pop('collection_id')]
                    except (OperationalError, ValueError) as err:
                        # raise web.HTTPBadRequest(text=json.dumps({'errors': [str(err)]}))
                        collections = {}
                # /v1 keeps collection
                res['data'][aliases.get(key, key)].extend(values)
        else:
            raise web.HTTPBadRequest(text=f'unknown rpc function "{func}"')

    return web.json_response(res)
