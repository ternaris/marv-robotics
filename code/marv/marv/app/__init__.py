# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import asyncio
import base64
import os
from collections import namedtuple
from logging import getLogger
from pathlib import Path

from aiohttp import web
from pkg_resources import resource_filename

import marv_webapi
from marv.collection import cached_property
from marv_api.utils import find_obj
from marv_webapi.tooling import safejoin

DOCS = Path(resource_filename('marv.app', 'docs'))
LOADED = False
log = getLogger(__name__)


async def site_load_for_web(aioapp):
    aioapp['site'].load_for_web()


async def destroy_site(aioapp):
    await aioapp['site'].destroy()


class App():
    STARTUP_FNS = (
        site_load_for_web,
    )

    SHUTDOWN_FNS = (
        destroy_site,
    )

    CACHE = {'Cache-Control': 'max-age=604800'}
    NOCACHE = {'Cache-Control': 'no-cache'}

    def __init__(self, site, app_root='', middlewares=None):
        self.aioapp = web.Application(middlewares=middlewares or [])
        self.aioapp['api_endpoints'] = {}
        self.aioapp['app_root'] = app_root.rstrip('/')
        self.aioapp['config'] = {
            'SECRET_KEY': site.config.marv.sessionkey_file.read_text(),
        }
        self.aioapp['debug'] = False
        self.aioapp['route_acl'] = find_obj(site.config.marv.acl)()
        self.aioapp['site'] = site
        self.aioapp.route = self.route

        for func in self.STARTUP_FNS:
            self.aioapp.on_startup.append(func)

        for func in self.SHUTDOWN_FNS:
            self.aioapp.on_shutdown.append(func)

        self.initialize_routes()

    def route(self, path):
        def dec(func):
            self.aioapp.add_routes([web.route('GET', f'{self.aioapp["app_root"]}{path}', func)])
        return dec

    @cached_property
    def index_html(self):
        path = self.aioapp['site'].config.marv.staticdir / 'index.html'
        index_html = path.read_text().replace('MARV_APP_ROOT', self.aioapp['app_root'] or '')

        frontenddir = self.aioapp['site'].config.marv.frontenddir
        for ext in ('css', 'js'):
            try:
                data = base64.b64encode((frontenddir / f'custom.{ext}').read_bytes()).decode()
            except IOError:
                pass
            else:
                placeholder = f'<!--custom.{ext}-->'
                assert placeholder in index_html
                script = f'<script src="data:text/javascript;base64,{data}"></script>' \
                         if ext == 'js' else \
                         f'<link rel="stylesheet" href="data:text/css;base64,{data}" />'
                index_html = index_html.replace(placeholder, script, 1)
        return index_html

    def initialize_routes(self):
        global LOADED  # pylint: disable=global-statement
        if not LOADED:
            marv_webapi.load_entry_points()
            LOADED = True
        marv_webapi.webapi.init_app(self.aioapp, url_prefix='/marv/api',
                                    app_root=self.aioapp['app_root'])
        aggressive_caching = bool(os.environ.get('MARV_EXPERIMENTAL_AGGRESSIVE_CACHING'))

        customdir = self.aioapp['site'].config.marv.frontenddir / 'custom'
        staticdir = self.aioapp['site'].config.marv.staticdir

        # decorator for non api endpoint routes
        @self.route('/custom/{path:.*}')
        async def custom(request):  # pylint: disable=unused-variable
            path = request.match_info['path']
            fullpath = safejoin(customdir, path)
            if not fullpath.is_file():
                raise web.HTTPNotFound
            return web.FileResponse(fullpath, headers=self.NOCACHE)

        @self.route(r'/docs{_:/?}{path:((?<=/).*)?}')
        async def docs(request):  # pylint: disable=unused-variable
            path = request.match_info['path'] or 'index.html'
            return web.FileResponse(safejoin(DOCS, path), headers={'Cache-Control': 'no-cache'})

        @self.route('/{path:.*}')
        async def assets(request):  # pylint: disable=unused-variable
            path = request.match_info['path'] or 'index.html'
            if path == 'index.html':
                return web.Response(text=self.index_html, headers={
                    'Content-Type': 'text/html',
                    **self.NOCACHE,
                })

            fullpath = safejoin(staticdir, path)
            if not fullpath.is_file():
                raise web.HTTPNotFound

            headers = (self.CACHE if aggressive_caching and fullpath.suffix == '.svg' else
                       self.NOCACHE)
            return web.FileResponse(fullpath, headers=headers)
