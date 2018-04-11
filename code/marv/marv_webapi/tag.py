# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

from itertools import cycle

import flask

from marv.model import Tag, dataset_tag, db
from .tooling import api_endpoint as marv_api_endpoint


@marv_api_endpoint('/tag', methods=['POST'])
def tag():
    # TODO: very similar to cli marv_tag
    changes = flask.request.get_json()
    if not changes:
        flask.abort(400)

    for collection, ops in changes.items():
        if collection not in flask.current_app.site.collections:
            flask.abort(400)

        addop = ops.get('add', {})
        removeop = ops.get('remove', {})

        add = addop.viewkeys()
        remove = removeop.viewkeys()

        if add:
            stmt = Tag.__table__.insert().prefix_with('OR IGNORE')
            db.session.execute(stmt, [{'collection': collection,
                                       'value': x} for x in add])

        if add or remove:
            tags = {value: id for id, value in (db.session.query(Tag.id, Tag.value)
                                                .filter(Tag.collection == collection)
                                                .filter(Tag.value.in_(add | remove)))}

        if add:
            stmt = dataset_tag.insert().prefix_with('OR IGNORE')
            values = [{'tag_id': x, 'dataset_id': y} for tag, ids in addop.items()
                      for x, y in zip(cycle([tags[tag]]), ids)]
            db.session.execute(stmt, values)

        if remove:
            where = reduce(lambda acc, x: acc | x, (
                ((dataset_tag.c.tag_id == x) & (dataset_tag.c.dataset_id == y))
                for tag, ids in removeop.items()
                for x, y in zip(cycle([tags[tag]]), ids)
            ))
            stmt = dataset_tag.delete().where(where)
            db.session.execute(stmt)

    db.session.commit()

    # TODO: report about unprocessed "setids"
    return flask.jsonify({})
