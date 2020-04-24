# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import base64
import os
from logging import getLogger
from pathlib import Path

from aiohttp import web

import marv_webapi
from marv_webapi.tooling import safejoin


LOADED = False
log = getLogger(__name__)


def create_app(site, app_root='', middlewares=None):  # noqa: C901  # pylint: disable=too-many-statements
    app = web.Application(middlewares=middlewares or [])
    app['acl'] = site.config.marv.acl()
    app['api_endpoints'] = {}
    app['config'] = {}
    app['debug'] = False
    app['site'] = site

    app_root = app_root.rstrip('/')

    # decorator for non api endpoint routes
    def route(path):
        def dec(func):
            app.add_routes([web.route('GET', f'{app_root}{path}', func)])
        return dec
    app.route = route

    site.load_for_web()

    async def shutdown(app):  # pylint: disable=unused-argument
        await site.destroy()
    app.on_shutdown.append(shutdown)
    global LOADED  # pylint: disable=global-statement
    if not LOADED:
        marv_webapi.load_entry_points()
        LOADED = True
    marv_webapi.webapi.init_app(app, url_prefix='/marv/api', app_root=app_root)

    with open(site.config.marv.sessionkey_file) as f:
        app['config']['SECRET_KEY'] = f.read()

    staticdir = Path(site.config.marv.staticdir)
    index_html = (staticdir / 'index.html').read_text().replace('MARV_APP_ROOT', app_root or '')

    try:
        data = base64.b64encode(Path(site.config.marv.frontenddir, 'custom.js').read_text())
    except IOError:
        pass
    else:
        assert '<script async src="main-built.js"></script>' in index_html
        index_html = index_html.replace(
            '<script async src="main-built.js"></script>',
            (
                f'<script src="data:text/javascript;base64,{data}"></script>\n'
                '<script async src="main-built.js"></script>'
            ),
            1,
        )

    try:
        data = base64.b64encode(Path(site.config.marv.frontenddir, 'custom.css').read_text())
    except IOError:
        pass
    else:
        assert '<link async rel="stylesheet" href="main-built.css" />' in index_html
        index_html = index_html.replace(
            '<link async rel="stylesheet" href="main-built.css" />',
            (
                '<link async rel="stylesheet" href="main-built.css" />'
                f'<link rel="stylesheet" href="data:text/css;base64,{data}" />'
            ),
            1,
        )

    nocache = {'Cache-Control': 'no-cache'}

    customdir = Path(site.config.marv.frontenddir, 'custom')
    @app.route('/custom/{path:.*}')
    async def custom(request):  # pylint: disable=unused-variable
        path = request.match_info['path']
        fullpath = safejoin(customdir, path)
        if not fullpath.is_file():
            raise web.HTTPNotFound
        return web.FileResponse(fullpath, headers=nocache)

    @app.route('/{path:.*}')
    async def assets(request):  # pylint: disable=unused-variable
        path = request.match_info['path'] or 'index.html'
        if path == 'index.html':
            return web.Response(text=index_html, headers={
                'Content-Type': 'text/html',
                **nocache,
            })

        fullpath = safejoin(staticdir, path)
        if not fullpath.is_file():
            raise web.HTTPNotFound
        return web.FileResponse(fullpath, headers=nocache)

    return app
