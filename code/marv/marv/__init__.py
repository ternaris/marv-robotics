# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import sys

from pkg_resources import iter_entry_points

from marv_node.io import Abort
from marv_node.io import create_group
from marv_node.io import create_stream
from marv_node.io import fork
from marv_node.io import get_logger
from marv_node.io import get_requested
from marv_node.io import get_stream
from marv_node.io import make_file
from marv_node.io import pull
from marv_node.io import pull_all
from marv_node.io import push
from marv_node.io import set_header
from marv_node.node import input, node
from marv_node.tools import select
from marv_webapi.tooling import api_endpoint
from marv_webapi.tooling import api_group

__all__ = [
    'Abort',
    'api_endpoint',
    'api_group',
    'create_group',
    'create_stream',
    'fork',
    'get_logger',
    'get_requested',
    'get_stream',
    'input',
    'make_file',
    'node',
    'pull',
    'pull_all',
    'push',
    'select',
    'set_header',
]

MODULE = sys.modules[__name__]
for ep in iter_entry_points(group='marv_deco'):
    assert not hasattr(MODULE, ep.name)
    setattr(MODULE, ep.name, ep.load())
del MODULE
