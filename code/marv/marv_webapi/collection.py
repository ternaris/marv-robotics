# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import json
from json import dumps as jsondumps

import flask
from flask import current_app, request
from sqlalchemy.sql import select

from marv.collection import Filter, UnknownOperator
from marv.model import STATUS, Tag, db
from marv.utils import parse_datetime, parse_filesize
from .tooling import APIEndpoint, api_endpoint as marv_api_endpoint


ALIGN = {
    'filesize': 'right',
    'icon': 'center',
    'int': 'right',
    'timedelta': 'right',
}


FILTER_PARSER = {
    'datetime': lambda x: int(
        (parse_datetime(x) - parse_datetime('1970-01-01T00:00:00+00:00'))
        .total_seconds() * 1000
    ),
    'filesize': parse_filesize,
    'float': float,
    'int': int,
    'string': str,
    'string[]': str,
    'subset': lambda x: x,
    'timedelta': lambda x: x,
    'words': lambda x: x.split(),
}


VALUE_TYPE_MAP = {
    'string[]': 'string',
    'words': 'string',
}


# Order corresponds to marv.model.STATUS OrderedDict
STATUS_ICON = ['fire', 'eye-close', 'warning-sign', 'time']
STATUS_JSON = [jsondumps({'icon': STATUS_ICON[i], 'title': x},
                         separators=(',', ':'))
               for i, x in enumerate(STATUS.values())]
# TODO: reconsider in case we get a couple of more states
STATUS_STRS = {
    bitmask: ','.join(filter(None,
                             [STATUS_JSON[i] if bitmask & 2**i else None
                              for i in range(len(STATUS_JSON))]))
    for bitmask in range(2**(len(STATUS_JSON)))
}


class FilterParseError(Exception):
    pass


def parse_filters(specs, filters):
    filters = json.loads(filters)
    filters = [Filter(k, FILTER_PARSER[specs[k].value_type](v['val']), v['op'])
               for k, v in filters.items()]
    return filters


@marv_api_endpoint('/meta', force_acl=['__unauthenticated__', '__authenticated__'])
def meta():
    groups = request.user_groups

    collection_acl = current_app.acl['collection']
    if '__unauthenticated__' not in collection_acl and not request.username:
        return flask.jsonify({
            'realms': current_app.site.config.marv.oauth.keys(),
        })

    # TODO: avoid clashes, forbid routes with same name / different name generation
    acl = sorted([
        name.split('.')[-1]
        for name, view in current_app.view_functions.viewitems()
        if isinstance(view, APIEndpoint)
        if view.acl.intersection(groups)
    ])

    # TODO: id probably numeric, title = name or title
    collections = current_app.site.collections
    collection_id = collections.default_id
    return flask.jsonify({
        'collections': {
            'default': collection_id,
            'items': [{'id': x, 'title': x} for x in collections.keys()],
        },
        'acl': acl,
        'realms': current_app.site.config.marv.oauth.keys(),
    })


@marv_api_endpoint('/collection', defaults={'collection_id': None})
@marv_api_endpoint('/collection/<collection_id>')
def collection(collection_id):
    collections = current_app.site.collections
    collection_id = collections.default_id if collection_id is None else collection_id
    try:
        collection = collections[collection_id]
    except KeyError:
        flask.abort(404)

    try:
        filters = parse_filters(collection.filter_specs,
                                request.args.get('filter', '{}'))
    except (KeyError, ValueError):
        current_app.logger.warn('Bad request', exc_info=True)
        return flask.abort(400)

    try:
        stmt = collection.filtered_listing(filters)
    except UnknownOperator:
        current_app.logger.warn('Bad request', exc_info=True)
        flask.abort(400)

    fspecs = collection.filter_specs

    all_known = {
        name: [x[0] for x in
               db.session.execute(select([rel.value])
                                  .order_by(rel.value)).fetchall()]
        for name, rel in collection.model.relations.items()
        if {'any', 'all'}.intersection(fspecs[name].operators)
    }
    all_known['status'] = STATUS.keys()
    all_known['tags'] = [x[0] for x in
                         db.session.execute(select([Tag.value])
                                            .where(Tag.collection == collection.name)
                                            .order_by(Tag.value)).fetchall()]
    filters = [{'key': x.name,
                'constraints': all_known.get(x.name),
                'title': x.title,
                'operators': x.operators,
                'value_type': VALUE_TYPE_MAP.get(x.value_type, x.value_type)}
               for x in fspecs.values()]

    rows = db.session.execute(stmt).fetchall()
    rowdata = ',\n'.join([x.replace('["#TAGS#"]', tags if tags != '[null]' else '[]')
                          .replace('"#TAGS#"', tags[1:-1] if tags != '[null]' else '')
                          .replace('[,', '[')
                          .replace('"#STATUS#"', STATUS_STRS[status])
                          for x, status, tags in rows])
    dct = {
        'all_known': all_known,
        'compare': bool(collection.compare),
        'filters': {'title': 'Filter',
                    'widget': {'type': 'filter', 'filters': filters}},
        'summary_config': {'title': 'Summary', 'items': collection.summary_items},
        'listing': {'title': 'Data sets ({} found)'.format(len(rows)),
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
    if current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] and not request.is_xhr:
        indent = 2
        separators = (', ', ': ')
    jsondata = jsondumps(dct, indent=indent, separators=separators, sort_keys=True)
    jsondata = jsondata.replace('"#ROWS#"', rowdata)
    return current_app.response_class(
        (jsondata, '\n'), mimetype=current_app.config['JSONIFY_MIMETYPE'])
