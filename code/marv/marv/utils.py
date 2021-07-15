# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import os
import re
import sys
import time
from datetime import datetime, timedelta
from datetime import tzinfo as tzinfo_base
from itertools import islice

from marv_api.utils import NOTSET


def chunked(iterable, chunk_size):
    itr = iter(iterable)
    return iter(lambda: tuple(islice(itr, chunk_size)), ())


def findfirst(predicate, iterable, default=NOTSET):
    try:
        return next(x for x in iterable if predicate(x))
    except StopIteration:
        if default is not NOTSET:
            return default
        raise ValueError('No item matched predicate!')


def mtime(path):
    """Wrap os.stat() st_mtime for ease of mocking."""
    return os.stat(path).st_mtime


def stat(path):
    """Wrap os.stat() for ease of mocking."""  # noqa: D402
    # TODO: https://github.com/PyCQA/pydocstyle/issues/284
    return os.stat(path)


def walk(path):
    """Wrap os.walk() for ease of mocking."""  # noqa: D402
    # TODO: https://github.com/PyCQA/pydocstyle/issues/284
    return os.walk(path)


def now():
    """Wrap time.time() for ease of mocking."""
    return time.time()


def parse_filesize(string):
    val, unit = re.match(r'^\s*([0-9.]+)\s*([kmgtpezy]b?)?\s*$', string, re.I)\
                  .groups()
    val = float(val)
    if unit:
        val *= 1 << (10 * (1 + 'kmgtpezy'.index(unit.lower()[0])))
    return int(val)


def parse_datetime(string):
    class TZInfo(tzinfo_base):
        def __init__(self, offset=None):
            self.offset = offset

        def dst(self, dt):
            raise NotImplementedError()

        def tzname(self, dt):
            return self.offset

        def utcoffset(self, dt):
            if self.offset == 'Z':
                hours, minutes = 0, 0
            else:
                hours, minutes = self.offset[1:].split(':')
            offset = timedelta(hours=int(hours), minutes=int(minutes))
            return offset if self.offset[0] == '+' else -offset

    groups = re.match(r'^(\d\d\d\d)-(\d\d)-(\d\d)T'
                      r'(\d\d):(\d\d):(\d\d)((?:[+-]\d\d:\d\d)|Z)$', string)\
               .groups()
    tzinfo = TZInfo(groups[-1])
    return datetime(*(int(x) for x in groups[:-1]), tzinfo=tzinfo)


def parse_timedelta(delta):
    match = re.match(r'^\s*(?:(\d+)\s*h)?'
                     r'\s*(?:(\d+)\s*m)?'
                     r'\s*(?:(\d+)\s*s?)?\s*$', delta)
    h, m, s = match.groups() if match else (None, None, None)  # pylint: disable=invalid-name
    return (int(h or 0) * 3600 + int(m or 0) * 60 + int(s or 0)) * 1000


def profile(func, sort='cumtime'):
    # pylint: disable=import-outside-toplevel
    import functools
    import pstats
    from cProfile import Profile
    _profile = Profile()

    @functools.wraps(func)
    def profiled(*args, **kw):
        _profile.enable()
        result = func(*args, **kw)
        _profile.disable()
        stats = pstats.Stats(_profile).sort_stats(sort)
        stats.print_stats()
        return result
    return profiled


def underscore_to_camelCase(string):  # pylint: disable=invalid-name
    return ''.join(x.capitalize() for x in string.split('_'))


def within_pyinstaller_bundle():
    return any(x.endswith('base_library.zip') for x in sys.path)


def within_staticx_bundle():
    return bool(os.environ.get('STATICX_PROG_PATH'))
