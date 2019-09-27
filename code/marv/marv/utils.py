# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import os
import re
import time
from datetime import datetime, timedelta
from datetime import tzinfo as tzinfo_base
from importlib import import_module
from itertools import islice

from marv_node.setid import decode_setid, encode_setid  # pylint: disable=unused-import


def chunked(iterable, chunk_size):
    itr = iter(iterable)
    return iter(lambda: tuple(islice(itr, chunk_size)), ())


def find_obj(objpath, name=False):
    modpath, objname = objpath.split(':')
    mod = import_module(modpath)
    obj = getattr(mod, objname)
    return (objname, obj) if name else obj


def mtime(path):
    """Wrap os.stat() st_mtime for ease of mocking."""
    return os.stat(path).st_mtime


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
