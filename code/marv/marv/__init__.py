# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import marv_api
from marv_api import deprecation
from marv_node.io import Abort
from marv_node.io import create_group
from marv_node.io import create_stream
from marv_node.io import get_logger
from marv_node.io import get_requested
from marv_node.io import make_file
from marv_node.io import pull
from marv_node.io import pull_all
from marv_node.io import push
from marv_node.io import set_header
from marv_node.node import input, node
from marv_webapi.tooling import api_endpoint as _api_endpoint
from marv_webapi.tooling import api_group as _api_group

DEPRECATIONS = {
    'api_endpoint': deprecation.Info(__name__, '20.07', _api_endpoint),
    'api_group': deprecation.Info(__name__, '20.07', _api_group),
    'select': deprecation.Info(
        __name__, '20.07', marv_api.select,
        'Use marv_api.select instead: import marv_api as marv.',
    ),
}

__all__ = [
    'Abort',
    'create_group',
    'create_stream',
    'get_logger',
    'get_requested',
    'input',
    'make_file',
    'node',
    'pull',
    'pull_all',
    'push',
    'set_header',
]

__dir__, __getattr__ = deprecation.dir_and_getattr(__name__, __all__, DEPRECATIONS)
