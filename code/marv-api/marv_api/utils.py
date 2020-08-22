# Copyright 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import sys
from importlib import import_module

NOTSET = type('NOTSET', (tuple,), {'__repr__': lambda x: '<NOTSET>'})()


def echo(*args, **kw):
    """Wrap print to let linter forbid print usage."""
    print(*args, **kw)  # noqa: T001


def err(*args, exit=None, **kw):
    """Print to stderr and optionally exit."""
    print(*args, **kw, file=sys.stderr, flush=True)  # noqa: T001
    if exit is not None:
        sys.exit(exit)


def find_obj(objpath, name=False):
    try:
        modpath, objname = objpath.split(':')
    except ValueError:
        modpath, objname = objpath.rsplit('.', 1)
    mod = import_module(modpath)
    obj = getattr(mod, objname)
    return (objname, obj) if name else obj


def exclusive_setitem(dct, key, value, exc_class=KeyError):
    if key in dct:
        raise exc_class(f'{key!r} already in dictionary')
    dct[key] = value


def popattr(obj, name, default=NOTSET):
    try:
        value = getattr(obj, name)
        delattr(obj, name)
        return value
    except AttributeError:
        if default is NOTSET:
            raise
        return default
