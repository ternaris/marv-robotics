# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from functools import reduce
from itertools import cycle

from aiohttp import web

from marv.model import Tag, dataset_tag, scoped_session
from .tooling import api_endpoint as marv_api_endpoint


@marv_api_endpoint('/tag', methods=['POST'])
async def tag(request):
    # TODO: very similar to cli marv_tag
    changes = await request.json()
    if not changes:
        raise web.HTTPBadRequest()

    with scoped_session(request.app['site']) as session:
        for collection, ops in changes.items():
            if collection not in request.app['site'].collections:
                raise web.HTTPBadRequest()

            addop = ops.get('add', {})
            removeop = ops.get('remove', {})

            add = addop.keys()
            remove = removeop.keys()

            if add:
                stmt = Tag.__table__.insert().prefix_with('OR IGNORE')
                session.execute(stmt, [{'collection': collection,
                                        'value': x} for x in add])

            if add or remove:
                tags = {value: id for id, value in (session.query(Tag.id, Tag.value)
                                                    .filter(Tag.collection == collection)
                                                    .filter(Tag.value.in_(add | remove)))}

            if add:
                stmt = dataset_tag.insert().prefix_with('OR IGNORE')  # pylint: disable=no-value-for-parameter
                values = [{'tag_id': x, 'dataset_id': y} for tag, ids in addop.items()
                          for x, y in zip(cycle([tags[tag]]), ids)]
                session.execute(stmt, values)

            if remove:
                where = reduce(lambda acc, x: acc | x, (
                    ((dataset_tag.c.tag_id == x) & (dataset_tag.c.dataset_id == y))
                    for tag, ids in removeop.items()
                    for x, y in zip(cycle([tags[tag]]), ids)
                ))
                stmt = dataset_tag.delete().where(where)  # pylint: disable=no-value-for-parameter
                session.execute(stmt)

    # TODO: report about unprocessed "setids"
    return web.json_response({})
