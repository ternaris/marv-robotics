# Copyright 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from importlib import import_module

NOTSET = type('NOTSET', (tuple,), {'__repr__': lambda x: '<NOTSET>'})()


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
