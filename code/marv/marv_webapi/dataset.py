# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import json
import os

import flask
from flask import current_app

from marv.model import Comment, Dataset, File, Tag, dataset_tag, db
from marv_node.setid import SetID
from .tooling import api_group as marv_api_group


@marv_api_group()
def dataset(app):
    pass


@dataset.endpoint('/file-list', methods=['POST'])
def file_list():
    ids = flask.request.get_json()
    if not ids:
        flask.abort(400)

    # TODO: remove scanroot prefix?

    query = db.session.query(File.path)\
                      .filter(File.dataset_id.in_(ids))\
                      .order_by(File.path)
    paths = [x[0] for x in query]

    query = db.session.query(Dataset.setid, File.idx)\
                      .filter(Dataset.id.in_(ids))\
                      .join(File)\
                      .order_by(Dataset.setid)
    urls = ['dataset/{}/{}'.format(setid, idx)
            for setid, idx in query]

    # TODO: complain about invalid/unknown ids?

    return flask.jsonify({'paths': paths, 'urls': urls})


@dataset.endpoint('/dataset/<setid>', defaults={'path': None})
@dataset.endpoint('/dataset/<setid>/<path:path>')
def detail(setid, path):
    try:
        setid = str(SetID(setid))
    except TypeError:
        flask.abort(404)

    setdir = os.path.join(current_app.site.config.marv.storedir, setid)

    # dataset file download
    try:
        idx = int(path)
    except (TypeError, ValueError):
        pass
    else:
        path = db.session.query(File.path)\
                         .join(Dataset)\
                         .filter(Dataset.setid == setid)\
                         .filter(File.idx == idx)\
                         .scalar()
        try:
            return flask.send_file(path, as_attachment=True, conditional=True)
        except ValueError:
            flask.abort(404)

    try:
        if path:
            return flask.send_from_directory(setdir, path, conditional=True)
        with open(os.path.join(setdir, 'detail.json')) as f:
            detail = json.load(f)
    except IOError:
        return flask.abort(404)

    # TODO: investigate merge into one
    dataset_id, collection = db.session.query(Dataset.id, Dataset.collection)\
                                       .filter(Dataset.setid == setid)\
                                       .one()
    comments = db.session.query(Comment.author, Comment.time_added, Comment.text)\
                         .filter(Comment.dataset_id == dataset_id)\
                         .order_by(Comment.time_added)
    detail['comments'] = [{'author': x[0],
                           'timeAdded': x[1],
                           'text': x[2]} for x in comments]

    collection = current_app.site.collections[collection]
    alltags = db.session.query(Tag.value)\
                        .filter(Tag.collection == collection.name)\
                        .order_by(Tag.value)
    detail['all_known_tags'] = [x[0] for x in alltags]

    tags = db.session.query(Tag.value)\
                     .join(dataset_tag)\
                     .filter(dataset_tag.c.dataset_id == dataset_id)\
                     .order_by(Tag.value)
    detail['tags'] = [x[0] for x in tags]
    detail['collection'] = collection.name
    detail['id'] = dataset_id
    detail['setid'] = setid
    return flask.jsonify(detail)
