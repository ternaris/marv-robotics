# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

"""Marv config parsing."""

import sys
import sysconfig
from configparser import ConfigParser
from functools import partial
from logging import getLogger
from pathlib import Path
from typing import Dict, Optional, Tuple

from pkg_resources import resource_filename
from pydantic import BaseModel, Extra, validator

from marv_api.utils import echo, find_obj

from . import sexp

log = getLogger(__name__)


class ConfigError(Exception):
    def __str__(self):
        try:
            section, key, message = self.args  # pylint: disable=unbalanced-tuple-unpacking
        except ValueError:
            section, key = self.args  # pylint: disable=unbalanced-tuple-unpacking
            message = 'missing'
        return f'{section.filename} [{section.name}] {key}: {message}'


class InvalidToken(Exception):
    pass


def make_funcs(dataset, setdir, store):
    """Functions available for listing columns and filters."""
    return {
        'cat': lambda *lists: [x for lst in lists for x in lst],
        'comments': lambda: None,
        'detail_route': detail_route,
        'format': lambda fmt, *args: fmt.format(*args),
        'get': partial(getnode, dataset, setdir, store),
        'getitem': lambda x, y: x[y] if x is not None else None,
        'join': lambda sep, *args: sep.join([x for x in args if x]),
        'len': len,
        'link': (lambda href, title, target=None:
                 {'href': href or '',
                  'title': title or '',
                  'target': '_blank' if target is None else target}),
        'list': lambda *x: filter(None, list(x)),
        'max': max,
        'min': min,
        'rsplit': lambda x, *args: x.rsplit(*args) if x else None,
        'split': lambda x, *args: x.split(*args) if x else None,
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
        'trace': print_trace,
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
    args = [calltree(x, funcs) if isinstance(x, tuple) else x for x in args]
    return func(*args)


def getdeps(functree, deps=None):
    deps = set() if deps is None else deps
    name, args = functree
    if name == 'get':
        deps.add(getnode(None, None, None, args[0], _name_only=True))
    else:
        for arg in args:
            if isinstance(arg, tuple):
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


def getnode(dataset, setdir, store, objpath, default=None, _name_only=False):  # noqa: C901
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
    echo('TRACE', args)
    return args


def _parse_list(node):
    assert isinstance(node, sexp.List), node
    assert isinstance(node.args[0], sexp.Identifier), node.args[0]
    args = []
    for token in node.args[1:]:
        if isinstance(token, sexp.List):
            args.append(_parse_list(token))
        elif isinstance(token, sexp.Literal):
            args.append(token.value)
        else:
            raise InvalidToken(token)
    return (node.args[0].name, args)


def parse_function(string):
    tree = sexp.scan(string)
    return _parse_list(tree), tree.stop + 1  # pylint: disable=no-member


# pylint: disable=too-few-public-methods,no-self-argument,no-self-use


class Model(BaseModel):
    class Config:
        allow_mutation = False
        extra = Extra.forbid


class MarvConfig(Model):
    sitedir: Path  # TODO: workaround
    collections: str
    acl: Optional[str] = 'marv_webapi.acls:authenticated'
    dburi: Optional[str] = 'sqlite://db/db.sqlite'
    frontenddir: Optional[str] = 'frontend'
    oauth: Dict[str, Tuple[str, ...]] = ''
    reverse_proxy: Optional[str] = None
    sessionkey_file: Optional[str] = 'sessionkey'
    staticdir: Optional[str] = None
    storedir: Optional[str] = 'store'
    upload_checkpoint_commands: Optional[str] = ''
    venv: Optional[str] = 'venv'
    sitepackages: Optional[str] = None
    window_title: Optional[str] = ''

    @validator('acl', always=True)
    def find_obj(cls, value):
        return find_obj(value)

    @validator('collections', always=True)
    def space_separated_list(cls, value):
        if value is not None:
            return value.split()
        return None

    @validator('oauth', always=True, pre=True)
    def oauth_split(cls, value):
        if value is not None:
            return {
                line.split(' ', 1)[0]: [field.strip() for field in line.split('|')]
                for line in [x.strip() for x in value.splitlines()]
            }
        return None

    @validator('upload_checkpoint_commands', always=True)
    def cmd_lines(cls, value):
        if value is not None:
            return [x.split() for x in value.splitlines()]
        return None

    @validator('dburi', always=True)
    def dburi_prepend_sitedir(cls, value, values):
        if value.startswith('sqlite:///'):
            return value
        if value.startswith('sqlite://'):
            return f"sqlite://{values.get('sitedir')}/{value[9:]}"
        raise ValueError(f'Invalid dburi {value!r}')

    @validator('staticdir', pre=True)
    def staticdir_default(cls, value):
        if not value:
            return resource_filename('marv_ludwig', 'static')
        return value

    @validator('sitepackages', pre=True)
    def sitepackages_default(cls, value):
        if not value:
            return f'venv/lib/python{sysconfig.get_python_version()}/site-packages'
        return value

    @validator('frontenddir', 'sessionkey_file', 'staticdir', 'storedir', 'venv', 'sitepackages',
               always=True)
    def prepend_sitedir(cls, value, values):
        if Path(value).is_absolute():
            return value
        sitedir = values.get('sitedir')
        assert sitedir.is_absolute()
        return str(sitedir / value)

    @validator('sitedir', pre=True)
    def resolve_paths(cls, value):
        if value is not None:
            return Path(value).resolve()
        return None


class CollectionConfig(Model):
    sitedir: Path  # TODO: workaround
    scanner: str
    scanroots: Tuple[str, ...]
    compare: Optional[str] = None
    detail_summary_widgets: Tuple[str, ...] = """
    summary_keyval
    meta_table
    """
    detail_sections: Tuple[str, ...] = ''
    detail_title: str = '(get "dataset.name")'
    filters: Tuple[str, ...] = """
    name       | Name       | substring         | string   | (get "dataset.name")
    setid      | Set Id     | startswith        | string   | (get "dataset.id")
    size       | Size       | lt le eq ne ge gt | filesize | (sum (get "dataset.files[:].size"))
    status     | Status     | any all           | subset   | (status)
    tags       | Tags       | any all           | subset   | (tags)
    comments   | Comments   | substring         | string   | (comments)
    files      | File paths | substring_any     | string[] | (get "dataset.files[:].path")
    time_added | Added      | lt le eq ne ge gt | datetime | (get "dataset.time_added")
    """
    listing_columns: Tuple[str, ...] = """
    name       | Name   | route    | (detail_route (get "dataset.id") (get "dataset.name"))
    size       | Size   | filesize | (sum (get "dataset.files[:].size"))
    status     | Status | icon[]   | (status)
    tags       | Tags   | pill[]   | (tags)
    time_added | Added  | datetime | (get "dataset.time_added")
    """
    listing_sort: Tuple[str, ...] = '| ascending'
    listing_summary: Tuple[str, ...] = """
    datasets | datasets | int       | (len (rows))
    size     | size     | filesize  | (sum (rows "size" 0))
    """
    nodes: Tuple[str, ...] = """
    marv_nodes:dataset
    marv_nodes:meta_table
    marv_nodes:summary_keyval
    """

    @validator('compare', 'scanner')
    def find_obj(cls, value):
        if value:
            return find_obj(value)
        return None

    @validator('detail_title', always=True)
    def function(cls, value):
        # TODO: lookup node to fail early
        func, pos = parse_function(value)
        assert pos == len(value)
        return func

    @validator('detail_sections', 'detail_summary_widgets', 'filters', 'listing_columns',
               'listing_summary', 'nodes', always=True, pre=True)
    def lines(cls, value):
        if value is not None:
            return [x for x in [x.strip() for x in value.splitlines()] if x]
        return None

    @validator('listing_sort', always=True, pre=True)
    def pipe_separated_list(cls, value):
        if value is not None:
            return [x.strip() for x in value.split('|')]
        return None

    @validator('scanroots', always=True, pre=True)
    def path_lines(cls, value, values):
        if value:
            return [str(values.get('sitedir') / x.strip()) for x in value.splitlines()]
        return None


class Config(Model):
    filename: Path
    marv: MarvConfig
    collections: Dict[str, CollectionConfig]

    @classmethod
    def from_file(cls, path):
        path = Path(path).resolve()
        sitedir = path.parent
        parser = ConfigParser()
        with path.open() as f:
            parser.read_file(f)

        dct = {
            'collections': {},
            'filename': path,
        }
        for name, section in parser._sections.items():  # pylint: disable=protected-access
            section['sitedir'] = sitedir
            if name.startswith('collection'):
                dct['collections'][name.split(None, 1)[1]] = section
            else:
                dct[name] = section
        return cls.parse_obj(dct)
