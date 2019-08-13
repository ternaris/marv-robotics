# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import flask
from flask import current_app

from .tooling import api_group as marv_api_group, generate_token


@marv_api_group()
def auth(_):
    pass

@auth.endpoint('/auth', methods=['POST'], force_acl=['__unauthenticated__'])
def auth_post():
    req = flask.request.get_json()
    if not req:
        flask.abort(400)
    username = req.get('username', '')
    password = req.get('password', '').encode('utf-8')

    if not current_app.site.authenticate(username, password):
        return flask.abort(422)

    return flask.jsonify({'access_token': generate_token(username).decode('utf-8')})
