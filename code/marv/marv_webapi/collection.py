# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import json
from json import dumps as jsondumps

import pendulum
from aiohttp import web

from marv.collection import Filter
from marv.db import DBPermissionError, UnknownOperator
from marv.model import STATUS
from marv.utils import parse_datetime, parse_filesize, parse_timedelta

from .tooling import HTTPPermissionError
from .tooling import api_endpoint as marv_api_endpoint
from .tooling import get_global_granted, get_local_granted

ALIGN = {
    'acceleration': 'right',
    'distance': 'right',
    'filesize': 'right',
    'float': 'right',
    'icon': 'center',
    'int': 'right',
    'speed': 'right',
    'timedelta': 'right',
}


FILTER_PARSER = {
    'datetime': lambda x: int(
        (parse_datetime(x) - parse_datetime('1970-01-01T00:00:00+00:00')).total_seconds() * 1000,
    ),
    'filesize': parse_filesize,
    'float': float,
    'int': int,
    'string': str,
    'string[]': str,
    'subset': lambda x: x,
    'timedelta': parse_timedelta,
    'words': lambda x: x.split(),
}


VALUE_TYPE_MAP = {
    'string[]': 'string',
    'words': 'string',
}


TIMEZONE = pendulum.local_timezone().name


# Order corresponds to marv.model.STATUS OrderedDict
STATUS_ICON = ['fire', 'eye-close', 'warning-sign', 'time']
STATUS_JSON = [jsondumps({'icon': STATUS_ICON[i], 'title': x},
                         separators=(',', ':'))
               for i, x in enumerate(STATUS.values())]
# TODO: reconsider in case we get a couple of more states
STATUS_STRS = {
    bitmask: ','.join(filter(None,
                             (STATUS_JSON[i] if bitmask & 2**i else None
                              for i in range(len(STATUS_JSON)))))
    for bitmask in range(2**(len(STATUS_JSON)))
}


def parse_filters(specs, filters):
    return [
        # TODO: remove adding of f_ prefix after listing deprecation
        Filter(k if k.startswith('f_') else f'f_{k}',
               FILTER_PARSER[specs[k if k.startswith('f_') else f'f_{k}'].value_type](v['val']),
               v['op'],
               specs[k if k.startswith('f_') else f'f_{k}'].value_type)
        for k, v in filters.items()
    ]


@marv_api_endpoint('/meta', force_acl=['__unauthenticated__', '__authenticated__'], acl_key='list')
async def meta(request):
    site = request.app['site']
    if not set(request['user_groups']).intersection(request.app['route_acl']['list']):
        collections = []
    else:
        collections = await site.db.get_collections(user=request['username'])

    resp = web.json_response({
        'acl': get_global_granted(request),
        'collections': collections,
        'realms': list(site.config.marv.oauth),
        'timezone': TIMEZONE,
    })
    resp.headers['Cache-Control'] = 'no-cache'
    return resp


@marv_api_endpoint('/collection{_:/?}{collection_id:((?<=/).*)?}', acl_key='read')
async def collection(request):  # pylint: disable=too-many-locals  # noqa: C901
    site = request.app['site']
    collection_id = request.match_info['collection_id'] or site.collections.default_id

    try:
        all_known = await site.db.get_all_known_for_collection(site.collections, collection_id,
                                                               request['username'])
    except DBPermissionError:
        raise HTTPPermissionError(request)

    # try .. except for legacy reasons. will disappear with better data structuring
    try:
        collection = site.collections[collection_id]  # pylint: disable=redefined-outer-name
    except KeyError:
        raise web.HTTPNotFound()

    try:
        filters_dct = json.loads(request.query.get('filter', '{}'))
        filters = parse_filters(collection.filter_specs, filters_dct)
    except (KeyError, ValueError):
        raise web.HTTPBadRequest()

    try:
        rows = await site.db.get_filtered_listing(collection.table_descriptors, filters,
                                                  user=request['username'])
    except (KeyError, ValueError, UnknownOperator):
        raise web.HTTPBadRequest()

    real_id = next(
        x['id']
        for x in await site.db.get_collections(user=request['username'])
        if x['name'] == collection_id
    )
    acl = await site.db.get_acl('collection', real_id, request['username'],
                                get_local_granted(request))

    filters = [
        {
            'key': x.name,
            'constraints': all_known.get(x.name),
            'title': x.title,
            'operators': x.operators,
            'value_type': VALUE_TYPE_MAP.get(x.value_type, x.value_type),
        }
        for x in collection.filter_specs.values()
    ]

    def fmt(row):
        if not row['tag_value']:
            return '[]'
        return json.dumps(sorted(row['tag_value'].split(',')))

    rowdata = ',\n'.join([row['row'].replace('["#TAGS#"]', fmt(row))
                          .replace('"#TAGS#"', fmt(row)[1:-1] if fmt(row) != '[]' else '')
                          .replace('[,', '[')
                          .replace('"#STATUS#"', STATUS_STRS[row['status']])
                          for row in rows])
    dct = {
        'acl': acl,
        'all_known': all_known,
        'compare': bool(collection.compare),
        'filters': {'title': 'Filter',
                    'widget': {'type': 'filter', 'filters': filters}},
        'summary_config': {'title': 'Summary', 'items': collection.summary_items},
        'listing': {'title': f'Data sets ({len(rows)} found)',
                    'widget': {
                        'data': {
                            'columns': [{
                                'align': ALIGN.get(x.formatter, 'left'),
                                'formatter': x.formatter,
                                'sortkey': 'title' if x.formatter == 'route' else None,
                                'id': x.name,
                                'title': x.heading,
                                'list': x.islist,
                            } for x in collection.listing_columns],
                            'rows': ['#ROWS#'],
                            'sortcolumn': collection.sortcolumn,
                            'sortorder': collection.sortorder},
                        'type': 'table',
                    }},
    }
    indent = None
    separators = (',', ':')
    if request.app['debug']:
        indent = 2
        separators = (', ', ': ')
    jsondata = jsondumps(dct, indent=indent, separators=separators, sort_keys=True)
    jsondata = jsondata.replace('"#ROWS#"', rowdata)
    return web.Response(text=jsondata, headers={
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
    })
