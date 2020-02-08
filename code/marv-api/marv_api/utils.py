# Copyright 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from importlib import import_module

NOTSET = type('NOTSET', (tuple,), {'__repr__': lambda x: '<NOTSET>'})()


def find_obj(objpath, name=False):
    modpath, objname = objpath.split(':')
    mod = import_module(modpath)
    obj = getattr(mod, objname)
    return (objname, obj) if name else obj
