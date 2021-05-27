# Copyright 2016 - 2021  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import asyncio
import base64
import os
from collections import namedtuple
from logging import getLogger
from pathlib import Path

from aiohttp import web
from pkg_resources import resource_filename

from marv.collection import cached_property
from marv_api.utils import find_obj
from marv_webapi.api import api
from marv_webapi.tooling import Webapi, auth_middleware, safejoin

DOCS = Path(resource_filename('marv.app', 'docs'))
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
        self.aioapp = web.Application(middlewares=[*(middlewares or []), auth_middleware])
        self.aioapp['app_root'] = app_root.rstrip('/')
        self.aioapp['config'] = {
            'SECRET_KEY': site.config.marv.sessionkey_file.read_text(),
        }
        self.aioapp['debug'] = False
        self.aioapp['site'] = site

        for func in self.STARTUP_FNS:
            self.aioapp.on_startup.append(func)

        for func in self.SHUTDOWN_FNS:
            self.aioapp.on_shutdown.append(func)

        self.api = Webapi()
        self.api.endpoints.extend(api.endpoints)
        self.initialize_routes()

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
        aggressive_caching = bool(os.environ.get('MARV_EXPERIMENTAL_AGGRESSIVE_CACHING'))

        customdir = self.aioapp['site'].config.marv.frontenddir / 'custom'
        staticdir = self.aioapp['site'].config.marv.staticdir

        # decorator for non api endpoint routes
        @self.api.endpoint('/custom/{path:.*}', methods=['GET'], allow_anon=True)
        async def custom(request):  # pylint: disable=unused-variable
            path = request.match_info['path']
            fullpath = safejoin(customdir, path)
            if not fullpath.is_file():
                raise web.HTTPNotFound
            return web.FileResponse(fullpath, headers=self.NOCACHE)

        @self.api.endpoint(r'/docs{_:/?}{path:((?<=/).*)?}', methods=['GET'], allow_anon=True)
        async def docs(request):  # pylint: disable=unused-variable
            path = request.match_info['path'] or 'index.html'
            return web.FileResponse(safejoin(DOCS, path), headers={'Cache-Control': 'no-cache'})

        @self.api.endpoint('/{path:.*}', methods=['GET'], allow_anon=True)
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

        for ep in self.api.endpoints:
            name = ep.name
            path = f'{self.aioapp["app_root"]}{ep.url_rule}'
            for method in ep.methods:
                self.aioapp.add_routes([web.route(method, path, ep, name=name)])
