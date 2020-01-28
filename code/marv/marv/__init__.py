# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import marv_api
from marv_api import deprecation
from marv_webapi.tooling import api_endpoint as _api_endpoint
from marv_webapi.tooling import api_group as _api_group

DEPRECATIONS = {
    'api_endpoint': deprecation.Info(__name__, '20.07', _api_endpoint),
    'api_group': deprecation.Info(__name__, '20.07', _api_group),
}

DEPRECATIONS.update(
    (name, deprecation.Info(
        __name__, '20.07', getattr(marv_api, name),
        f'Use marv_api.{name} instead: import marv_api as marv.',
    )) for name in (
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
    )
)

__all__ = ()
__dir__, __getattr__ = deprecation.dir_and_getattr(__name__, __all__, DEPRECATIONS)
