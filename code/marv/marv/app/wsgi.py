# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import os
import sys

import marv.app
import marv.site
from marv_cli import setup_logging


async def create_app():
    setup_logging(os.environ.get('MARV_LOGLEVEL', 'info'))

    config = os.environ['MARV_CONFIG']
    init = os.environ.get('MARV_INIT')
    site = marv.site.Site(config, init=init)
    try:
        app_root = os.environ.get('MARV_APPLICATION_ROOT', '/')
        application = marv.app.create_app(site, app_root=app_root)
        site.load_for_web()
    except OSError as e:
        if e.errno == 13:
            print(e, file=sys.stderr)
            sys.exit(13)
        raise
    return application
