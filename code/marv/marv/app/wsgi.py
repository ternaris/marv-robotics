# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import os

import marv.app
import marv.site
from marv_cli import setup_logging
setup_logging(os.environ.get('MARV_LOGLEVEL', 'info'))

config = os.environ['MARV_CONFIG']
app_root = os.environ.get('MARV_APPLICATION_ROOT') or '/'
init = os.environ.get('MARV_INIT')

site = marv.site.Site(config)
site.load_for_web()
application = marv.app.create_app(site, app_root=app_root, init=init)
