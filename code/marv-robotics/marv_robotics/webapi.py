# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import os

import flask
from pkg_resources import resource_filename

from marv_webapi.tooling import api_group as marv_api_group


DOCS = os.path.join(resource_filename('marv_robotics', 'docs'))


@marv_api_group()
def robotics(app):

    @app.route('/docs', defaults={'path': 'index.html'})
    @app.route('/docs/', defaults={'path': 'index.html'})
    @app.route('/docs/<path:path>')
    def docs(path):
        return flask.send_from_directory(DOCS, path, conditional=True)
