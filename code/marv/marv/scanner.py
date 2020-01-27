# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from marv_api import (
    DatasetInfo as _DatasetInfo,
    deprecation,
)

__all__ = ()
__dir__, __getattr__ = deprecation.dir_and_getattr(__name__, __all__, {
    'DatasetInfo': deprecation.Info(__name__, '20.07', _DatasetInfo),
})
