# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import base64
import os
from logging import getLogger

from aiohttp import web

from marv_webapi import webapi


log = getLogger(__name__)


def create_app(site, app_root='', middlewares=None):  # noqa: C901
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
    webapi.init_app(app, url_prefix='/marv/api', app_root=app_root)

    with open(site.config.marv.sessionkey_file) as f:
        app['config']['SECRET_KEY'] = f.read()

    staticdir = site.config.marv.staticdir
    with open(os.path.join(staticdir, 'index.html')) as f:
        index_html = f.read().replace('MARV_APP_ROOT', app_root or '')

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
            (
                f'<script src="data:text/javascript;base64,{data}"></script>\n'
                '<script async src="main-built.js"></script>'
            ),
            1,
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
            (
                '<link async rel="stylesheet" href="main-built.css" />'
                f'<link rel="stylesheet" href="data:text/css;base64,{data}" />'
            ),
            1,
        )

    customdir = os.path.join(site.config.marv.frontenddir, 'custom')
    @app.route('/custom/{path}')
    async def custom(request):  # pylint: disable=unused-variable
        path = request.match_info['path']
        return web.FileResponse(os.path.join(customdir, path), headers={
            'Cache-Control': 'no-cache',
        })

    @app.route('/{path:.*}')
    async def assets(request):  # pylint: disable=unused-variable
        path = request.match_info['path']
        if not path:
            path = 'index.html'

        if path == 'index.html':
            return web.Response(text=index_html, headers={
                'Content-Type': 'text/html',
                'Cache-Control': 'no-cache',
            })

        if path == 'docs':
            raise web.HTTPMovedPermanently(f'{request.base_url}/')

        if path == 'docs/':
            path = 'docs/index.html'

        return web.FileResponse(os.path.join(staticdir, path), headers={
            'Cache-Control': 'no-cache',
        })

    return app
