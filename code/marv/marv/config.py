# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

"""Marv config parsing."""
from __future__ import absolute_import, division, print_function

import os
import sys
from inspect import getmembers
from collections import Mapping
from functools import partial
from logging import getLogger

from configparser import ConfigParser

from .utils import find_obj

log = getLogger(__name__)


class ConfigError(Exception):
    def __str__(self):
        try:
            section, key, message = self.args
        except ValueError:
            section, key = self.args
            message = 'missing'
        return '{} [{}] {}: {}'.format(section.filename, section.name, key, message)


def make_funcs(dataset, setdir, store):
    """Functions available for listing columns and filters."""
    return {
        'cat': lambda *lists: [x for lst in lists for x in lst],
        'comments': lambda: None,
        'detail_route': detail_route,
        'format': lambda fmt, *args: fmt.format(*args),
        'get': partial(getnode, dataset, setdir, store),
        'join': lambda sep, *args: sep.join([x for x in args if x]),
        'len': len,
        'link': (lambda href, title, target=None:
                 {'href': href or "",
                  'title': title or "",
                  'target': '_blank' if target is None else target}),
        'list': lambda *x: filter(None, list(x)),
        'max': max,
        'min': min,
        'status': lambda: ['#STATUS#'],
        'sum': sum,
        'tags': lambda: ['#TAGS#'],
        'trace': print_trace,
    }


def make_summary_funcs(rows, ids):
    """Functions available for listing summary fields."""
    return {
        'len': len,
        'list': lambda *x: filter(None, list(x)),
        'max': max,
        'min': min,
        'rows': partial(summary_rows, rows, ids),
        'sum': sum,
        'trace': print_trace
    }


def summary_rows(rows, ids, id=None, default=None):
    if not id:
        return rows
    idx = ids.index(id)
    return [default if value is None else value
            for value in (x['values'][idx] for x in rows)]


def calltree(functree, funcs):
    name, args = functree
    func = funcs[name]
    args = [calltree(x, funcs) if type(x) == tuple else x for x in args]
    return func(*args)


def getdeps(functree, deps=None):
    deps = set() if deps is None else deps
    name, args = functree
    if name == 'get':
        deps.add(getnode(None, None, None, args[0], _name_only=True))
    else:
        for arg in args:
            if type(arg) == tuple:
                getdeps(arg, deps)
    return deps


def detail_route(setid, name=None):
    return {
        'route': 'detail',
        'id': str(setid),
        'title': name if name else str(setid),
    }


def doget(value, name, lookup):
    value = getattr(value, name, None)
    if value is None:
        return None
    if lookup is not None:
        try:
            return value[lookup]
        except IndexError:
            return None
    return value


def getnode(dataset, setdir, store, objpath, default=None, _name_only=False):
    try:
        nodename, rest = objpath.split('.', 1)
    except ValueError:
        nodename, rest = objpath, None
    nodename, lookup = parse_lookup(nodename, 0)

    if _name_only:
        return nodename

    try:
        node = store.nodes[nodename]
    except KeyError:
        log.critical('Config error: unknown node %s', nodename)
        sys.exit(1)

    if node.name == 'dataset':
        msgs = node.load(setdir, dataset)
    else:
        try:
            msgs = store.load(setdir, node)
        except IOError:  # TODO: Dedicated exception
            return default

    try:
        value = msgs[lookup]
    except IndexError:
        return default

    # traverse the rest
    while rest:
        try:
            name, rest = rest.split('.', 1)
        except ValueError:
            name, rest = rest, None
        name, lookup = parse_lookup(name)
        if isinstance(value, list):
            value = [doget(x, name, lookup) for x in value]
        else:
            value = doget(value, name, lookup)
    return value


def parse_lookup(name, default=None):
    if name.endswith(']'):
        name, lookup = name[:-1].split('[')
        if ':' in lookup:
            lookup = slice(*[int(x) if x else None for x in lookup.split(':')])
        else:
            lookup = int(lookup)
    else:
        lookup = default
    return name, lookup


def print_trace(args):
    print("TRACE", args)
    return args


def parse_function(s, pos=0):
    assert s[pos] == '(', s
    start = pos + 1
    end = len(s) - 1
    try:
        pos = s.index(' ', start)
    except ValueError:
        pos = end
    name = s[start:pos]
    pos += 1
    args = []
    functree = (name, args)
    while s[pos] != ')' and pos < end:
        if s[pos] == '(':
            #print('FUNC', pos, s[pos:])
            func, pos = parse_function(s, pos)
            args.append(func)
        elif s[pos:pos+2] == '[]':
            args.append([])
            pos += 2
        elif s[pos] == '"':
            #print('STR"', pos, s[pos:])
            start = pos + 1
            pos = s.index('"', start)
            args.append(s[start:pos])
            pos += 1
        elif s[pos] == "'":
            #print("STR'", pos, s[pos:])
            start = pos + 1
            pos = s.index("'", start)
            args.append(s[start:pos])
            pos += 1
        elif s[pos] == '0':
            args.append(0)
            pos += 1
        elif s[pos] == ' ':
            pos += 1
        else:
            raise RuntimeError(pos, s[pos:])
    return functree, pos + 1


class Section(Mapping):
    def __init__(self, name, dct, filename, defaults=None, schema=None):
        self.name = name
        self._configdir = os.path.dirname(filename)
        self.filename = filename
        self._dct = dct
        self._defaults = defaults or {}
        self._schema = schema or {}

    def __dir__(self):
        return list(self._dct.viewkeys() | self.__dict__.viewkeys() |
                    {x[0] for x in getmembers(type(self))})

    def __getattr__(self, name):
        return self[name]

    def __getitem__(self, key):
        try:
            value = self._dct[key]
        except KeyError:
            value = self._defaults[key]
        if value is None:
            return None
        value = value.strip()
        value_type = self._schema.get(key)
        if value_type is not None:
            value = self._parse(value, value_type)
        return value

    def __iter__(self):
        return iter(list(self._dct.viewkeys() | self._defaults.viewkeys()))

    def __len__(self):
        return len(self._dct.viewkeys() | self._defaults.viewkeys())

    def _parse(self, value, value_type):
        if value_type == 'function':
            # TODO: lookup node to fail early
            func, pos = parse_function(value)
            assert pos == len(value)
            return func
        elif value_type == 'find_obj':
            return find_obj(value)
        elif value_type == 'lines':
            return [x.strip() for x in value.splitlines()]
        elif value_type == 'nodes':
            return [find_obj(x.strip()) for x in value.splitlines()]
        elif value_type == 'path':
            return self._abspath(value)
        elif value_type == 'path_lines':
            return [self._abspath(x.strip()) for x in value.splitlines()]
        elif value_type == 'pipe_separated_list':
            return [x.strip() for x in value.split('|')]
        elif value_type == 'space_separated_list':
            return value.split()
        else:
            raise ValueError('Unknown value_type %r' % value_type)

    def _abspath(self, value):
        if os.path.isabs(value):
            return value
        else:
            return os.path.realpath(os.path.join(self._configdir, value))


class Config(Mapping):
    def __init__(self, filename, sections):
        assert os.path.isabs(filename), filename
        self.filename = filename
        self._dct = sections

    @classmethod
    def from_file(cls, filename, defaults=None, required=None, schema=None):
        assert os.path.isabs(filename), filename
        defaults = defaults or {}
        schema = schema or {}

        # TODO: replace by own parser supporting line numbers
        parser = ConfigParser()
        with open(filename) as f:
            parser.read_file(f)

        sections = {
            k: Section(name=k, dct=v, filename=filename,
                       defaults=defaults.get(k) or defaults.get(k.split(None, 1)[0]),
                       schema=(schema.get(k) or schema.get(k.split(None, 1)[0])))
            for k, v in parser._sections.items()
        }
        if required:
            for name, section in sections.items():
                reqs = required.get(name) or required.get(name.split(None, 1)[0], [])
                for req in reqs:
                    if req not in section:
                        raise ConfigError(section, req)
        return cls(filename, sections)

    def __dir__(self):
        return list(self._dct.viewkeys() | self.__dict__.viewkeys() |
                    {x[0] for x in getmembers(type(self))})

    def __getattr__(self, name):
        return self[name]

    def __getitem__(self, key):
        return self._dct[key]

    def __iter__(self):
        return iter(self._dct)

    def __len__(self):
        return len(self._dct)
