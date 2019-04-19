# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import flask

from marv.model import Dataset, db
from .tooling import api_endpoint as marv_api_endpoint


@marv_api_endpoint('/dataset', methods=['DELETE'])
def delete():
    datasets = Dataset.__table__
    ids = flask.request.get_json()
    if not ids:
        flask.abort(400)
    stmt = datasets.update()\
                   .where(datasets.c.id.in_(ids))\
                   .values(discarded=True)
    db.session.execute(stmt)
    db.session.commit()
    return flask.jsonify({})
