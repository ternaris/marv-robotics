# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import json
import mimetypes
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


def _send_detail_json(setid, setdir):
    try:
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


@dataset.endpoint('/dataset/<setid>', defaults={'path': 'detail.json'})
@dataset.endpoint('/dataset/<setid>/<path:path>')
def detail(setid, path):
    try:
        setid = str(SetID(setid))
    except TypeError:
        flask.abort(404)

    setdir = os.path.join(current_app.site.config.marv.storedir, setid)

    if path == 'detail.json':
        return _send_detail_json(setid, setdir)

    if path.isdigit():
        path = db.session.query(File.path)\
                         .join(Dataset)\
                         .filter(Dataset.setid == setid)\
                         .filter(File.idx == int(path))\
                         .scalar()
    else:
        path = flask.safe_join(setdir, path)

    # Make sure path exists and is safe
    if not os.path.isabs(path) \
       or path != os.path.normpath(path) \
       or not os.path.isfile(path):
        return flask.abort(404)

    if current_app.site.config.marv.reverse_proxy == 'nginx':
        resp = flask.make_response()
        mime = mimetypes.guess_type(path)
        resp.headers['content-type'] = \
            mime[0] if mime[0] else 'application/octet-stream'
        resp.headers['cache-control'] = 'public, max-age=0'
        resp.headers['x-accel-buffering'] = 'no'
        resp.headers['x-accel-redirect'] = \
            (current_app.config['APPLICATION_ROOT'] or '') + path
        resp.headers.add('Content-Disposition', 'attachment',
                         filename=os.path.basename(path))
        return resp

    try:
        return flask.send_file(path, as_attachment=True, conditional=True)
    except ValueError:
        flask.abort(404)
