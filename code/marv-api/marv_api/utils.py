# Copyright 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import os
import sys
from contextlib import contextmanager
from importlib import import_module
from shlex import quote
from subprocess import Popen

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


def joincmd(cmd):
    """Join list of cmd and args into properly quoted string for shell execution."""
    return ' '.join([quote(x) for x in cmd])


@contextmanager
def launch_pdb_on_exception(launch=True):
    """Return contextmanager launching pdb on exception.

    Example:
      Toggle launch behavior via env variable::

          with launch_pdb_on_exception(os.environ.get('PDB')):
              cli()

    """
    if launch:
        try:
            yield
        except Exception:  # pylint: disable=broad-except
            import pdb  # pylint: disable=import-outside-toplevel
            pdb.xpm()  # pylint: disable=no-member
    else:
        yield


def popattr(obj, name, default=NOTSET):
    try:
        value = getattr(obj, name)
        delattr(obj, name)
        return value
    except AttributeError:
        if default is NOTSET:
            raise
        return default


def popen(*args, env=None, **kw):
    env = sanitize_env(os.environ.copy() if env is None else env)
    return Popen(*args, env=env, **kw)


def sanitize_env(env):
    ld_library_path = env.get('LD_LIBRARY_PATH')
    if ld_library_path:
        clean_path = ':'.join([
            x
            for x in ld_library_path.split(':')
            if not x.startswith('/tmp/_MEI')
        ])
        if clean_path:
            env['LD_LIBRARY_PATH'] = clean_path
        else:
            del env['LD_LIBRARY_PATH']
    return env
