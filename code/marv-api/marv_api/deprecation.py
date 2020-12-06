# Copyright 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import functools
import warnings
from dataclasses import dataclass
from typing import Any


@dataclass
class Info:
    module: str
    version: str
    obj: Any
    msg: str = None


def make_getattr(module, dct):
    assert all(x.module == module for x in dct.values())

    def __getattr__(name):
        info = dct.get(name)
        if info is None:
            raise AttributeError(f'module {module} has no attribute {name}')

        msg = (
            f'{module}.{name} will be removed in {info.version}; '
            f'{info.msg or "please let us know if this is an issue for you."}'
        )
        warnings.warn(msg, FutureWarning, stacklevel=2)
        return info.obj

    return __getattr__


def deprecated(version, msg=None, name=None):
    """Wrap function to trigger deprecated message upon call."""
    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            _msg = (
                f'{func.__module__}.{name or func.__name__} will be removed in {version}; '
                f'{msg or "please let us know if this is an issue for you."}'
            )
            warnings.warn(_msg, FutureWarning, stacklevel=2)
            return func(*args, **kw)
        return wrapper
    return deco
