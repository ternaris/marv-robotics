# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import time

import flask

from marv.model import Comment, Dataset, db
from .tooling import api_endpoint as marv_api_endpoint


@marv_api_endpoint('/comment', methods=['POST'])
def comment():
    username = flask.request.username
    changes = flask.request.get_json()
    if not changes:
        flask.abort(400)

    for id, ops in changes.items():
        now = int(time.time() * 1000)
        comments = [Comment(dataset_id=id, author=username, time_added=now, text=text)
                    for text in ops.get('add', [])]
        db.session.add_all(comments)
    db.session.commit()

    # TODO: inform about unknown setids?

    return flask.jsonify({})
