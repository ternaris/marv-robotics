# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

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
from marv_node.tools import select
from marv_webapi.tooling import api_endpoint as _api_endpoint
from marv_webapi.tooling import api_group as _api_group

DEPRECATIONS = {
    'api_endpoint': deprecation.Info(__name__, '20.07', _api_endpoint),
    'api_group': deprecation.Info(__name__, '20.07', _api_group),
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
    'select',
    'set_header',
]

__dir__, __getattr__ = deprecation.dir_and_getattr(__name__, __all__, DEPRECATIONS)
