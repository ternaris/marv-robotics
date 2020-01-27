# Copyright 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import warnings
from dataclasses import dataclass
from typing import Any


@dataclass
class Info:
    module: str
    version: str
    obj: Any
    msg: str = None


def dir_and_getattr(module, dunder_all, dct):
    assert all(x.module == module for x in dct.values())
    allattrs = tuple(set(dunder_all) | dct.keys())

    def __dir__():
        return allattrs

    def __getattr__(name):
        info = dct.get(name)
        if info is None:
            raise AttributeError(f'module {module} has no attribute {name}')

        msg = ' '.join([
            f'{module}.{name} will be removed in {info.version}.',
            info.msg or ' Please let us know if this is an issue for you.',
        ])
        warnings.warn(msg, FutureWarning, stacklevel=2)
        return info.obj

    return __dir__, __getattr__
