# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import base64
import os
from logging import getLogger

import flask
import sqlalchemy.exc

from marv_webapi import webapi
from ..model import db


log = getLogger(__name__)


class DBNotInitialized(Exception):
    pass


def create_app(site, config_obj=None, app_root=None, init=None, **kw):
    app = flask.Flask(__name__)
    app.site = site

    # default config
    app_root = app_root.rstrip('/') if app_root else None
    app.config['APPLICATION_ROOT'] = app_root or None
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['SQLALCHEMY_DATABASE_URI'] = site.config.marv.dburi
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if config_obj is not None:
        app.config.from_object(config_obj)
    app.config.update(kw)

    db.init_app(app)
    with app.app_context():
        if init:
            site.init()
        try:
            db.session.execute('SELECT name FROM sqlite_master WHERE type="table";')
        except sqlalchemy.exc.OperationalError:
            if init is None:  # auto-init
                site.init()
                db.session.execute('SELECT name FROM sqlite_master WHERE type="table";')
            else:
                raise DBNotInitialized()

        app.acl = site.config.marv.acl()
        webapi.init_app(app, url_prefix='/marv/api')

    with open(site.config.marv.sessionkey_file) as f:
        app.config['SECRET_KEY'] = f.read()

    staticdir = site.config.marv.staticdir
    with open(os.path.join(staticdir, 'index.html')) as f:
        index_html = f.read().replace('MARV_APP_ROOT', app_root or "")

    customjs = os.path.join(site.config.marv.frontenddir, 'custom.js')
    try:
        with(open(customjs)) as f:
            data = base64.b64encode(f.read())
    except IOError:
        pass
    else:
        assert '<script async src="main-built.js"></script>' in index_html
        index_html = index_html.replace(
            '<script async src="main-built.js"></script>',
            '<script src="data:text/javascript;base64,{}"></script>'.format(data) +
            '\n<script async src="main-built.js"></script>', 1
        )

    customcss = os.path.join(site.config.marv.frontenddir, 'custom.css')
    try:
        with(open(customcss)) as f:
            data = base64.b64encode(f.read())
    except IOError:
        pass
    else:
        assert '<link async rel="stylesheet" href="main-built.css" />' in index_html
        index_html = index_html.replace(
            '<link async rel="stylesheet" href="main-built.css" />',
            '<link async rel="stylesheet" href="main-built.css" />' +
            '<link rel="stylesheet" href="data:text/css;base64,{}" />'.format(data), 1
        )

    customdir = os.path.join(site.config.marv.frontenddir, 'custom')
    @app.route('/custom/<path:path>')
    def custom(path):
        return flask.send_from_directory(customdir, path, conditional=True)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def assets(path):
        if not path:
            path = 'index.html'

        if path == 'index.html':
            return index_html

        if path == 'docs':
            return flask.redirect(flask.request.base_url + '/', 301)

        if path == 'docs/':
            path = 'docs/index.html'

        return flask.send_from_directory(staticdir, path, conditional=True)

    return app
