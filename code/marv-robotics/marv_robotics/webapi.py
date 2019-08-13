# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import pathlib

from aiohttp import web
from pkg_resources import resource_filename

from marv_webapi.tooling import api_group as marv_api_group


DOCS = pathlib.Path(resource_filename('marv_robotics', 'docs'))


@marv_api_group()
def robotics(app):
    @app.route(r'/docs{_:/?}{path:((?<=/).*)?}')
    async def docs(request):  # pylint: disable=unused-variable
        path = request.match_info['path'] or 'index.html'
        return web.FileResponse(DOCS / path, headers={'Cache-Control': 'no-cache'})
