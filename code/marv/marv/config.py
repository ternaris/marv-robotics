# Copyright 2016 - 2021  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

"""Marv config parsing."""

import os
import sys
import sysconfig
from configparser import ConfigParser
from enum import Enum
from functools import partial
from logging import getLogger
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from pkg_resources import resource_filename
from pydantic import BaseModel, Extra, ValidationError, root_validator, validator

from marv_api.utils import echo

from . import sexp

log = getLogger(__name__)


class ConfigError(Exception):
    pass


class InvalidToken(Exception):
    pass


def make_funcs(dataset, setdir, store):
    """Functions available for listing columns and filters."""
    return {
        'cat': lambda *lists: [x for lst in lists for x in lst],
        'comments': lambda: None,
        'detail_route': detail_route,
        'filter': lambda x, y: list(filter(x, y)),
        'format': lambda fmt, *args: fmt.format(*args),
        'get': partial(getnode, dataset, setdir, store),
        'getitem': lambda x, y: x[y] if x is not None else None,
        'join': lambda sep, *args: sep.join([x for x in args if x]),
        'len': lambda x: len(x) if x is not None else None,
        'leaf': lambda x: f'#LEAF.{x}#',
        'link': (lambda href, title, target=None:
                 {'href': href or '',
                  'title': title or '',
                  'target': '_blank' if target is None else target}),
        'makelist': lambda *x: list(x),
        'max': lambda x: max(x) if x else None,
        'min': lambda x: min(x) if x else None,
        'rsplit': lambda x, *args: x.rsplit(*args) if x else None,
        'set': lambda x: set(x) if x else None,
        'split': lambda x, *args: x.split(*args) if x else None,
        'status': lambda: ['#STATUS#'],
        'sum': lambda x: sum(x) if x is not None else None,
        'tags': lambda: ['#TAGS#'],
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
    if isinstance(value, dict):
        value = value.get(name, None)
    else:
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
    assert tree.stop + 1 == len(string)  # pylint: disable=no-member
    return _parse_list(tree)


# pylint: disable=too-few-public-methods,no-self-argument,no-self-use


class Model(BaseModel):
    class Config:
        allow_mutation = False
        extra = Extra.forbid


class ReverseProxyEnum(str, Enum):
    nginx = 'nginx'


def resolve_path(val):
    if val is not None:
        return Path(val).resolve()
    return None


def resolve_relto_site(val, values):
    if val is not None:
        sitedir = values['sitedir']
        assert sitedir.is_absolute()
        return (sitedir / val).resolve()
    return None


def split(val):
    if val is not None:
        return val.split()
    return []


def splitcommastrip(val):
    if val is not None:
        return [x.strip() for x in val.split(',')]
    return []


def splitlines(val):
    if val is not None:
        return [stripped for x in val.splitlines() if (stripped := x.strip())]
    return []


def splitlines_relto_site(val, values):
    if val is not None:
        return [(values['sitedir'] / path).resolve()
                for x in val.splitlines()
                if (path := x.strip())]
    return []


def splitlines_split(val):
    if val is not None:
        return [stripped.split() for x in val.splitlines() if (stripped := x.strip())]
    return []


def splitpipe(val):
    if val is not None:
        return [x.strip() for x in val.split('|')]
    return []


def strip(val):
    if val is not None:
        return val.strip()
    return None


apvalidator = partial(validator, always=True, pre=True)
reapvalidator = partial(validator, allow_reuse=True, always=True, pre=True)


class MarvConfig(Model):
    sitedir: Path  # TODO: workaround
    collections: Tuple[str, ...]
    ce_anonymous_readonly_access: bool = False
    dburi: str = 'sqlite://db/db.sqlite'
    frontenddir: Path = 'frontend'
    leavesdir: Path = 'leaves'
    leafbinpath: Optional[Path] = None
    mail_footer: str = ''
    oauth: Dict[str, Tuple[str, ...]] = None
    oauth_enforce_username: Optional[str] = None
    oauth_gitlab_groups: Optional[Tuple[str, ...]] = None
    reverse_proxy: Optional[ReverseProxyEnum] = None
    resourcedir: Path = 'resources'
    sessionkey_file: Path = 'sessionkey'
    smtp_url: str = 'smtp://'
    smtp_from: str = ''
    staticdir: Path = resource_filename('marv', 'app/static')
    storedir: Path = 'store'
    upload_checkpoint_commands: Tuple[str, ...] = None
    venv: Path = 'venv'

    @property
    def sitepackages(self):
        return self.venv / 'lib' / f'python{sysconfig.get_python_version()}' / 'site-packages'

    _oauth_gitlab_groups = reapvalidator('oauth_gitlab_groups')(splitcommastrip)
    _resolve_path = reapvalidator('sitedir')(resolve_path)
    _resolve_relto_site = reapvalidator('frontenddir', 'leavesdir', 'resourcedir',
                                        'sessionkey_file', 'staticdir', 'storedir',
                                        'venv')(resolve_relto_site)
    _split = reapvalidator('collections')(split)
    _splitlines_split = reapvalidator('upload_checkpoint_commands')(splitlines_split)
    _strip = reapvalidator('reverse_proxy')(strip)

    @apvalidator('dburi')
    def dburi_relto_site(cls, val, values):
        if val and val.startswith('sqlite:///'):
            return val
        if val and val.startswith('sqlite://'):
            return f"sqlite://{(values['sitedir'] / val[9:]).resolve()}"
        raise ValueError(f'Invalid dburi {val!r}')

    @apvalidator('oauth')
    def oauth_split(cls, val):
        if val is not None:
            return {
                (fields := [x.strip() for x in line.split('|')])[0]: fields
                for x in val.splitlines()
                if (line := x.strip())
            }
        return {}

    @root_validator(pre=True)
    def root_validator(cls, values):
        if values.get('oauth_enforce_username') and len(values.get('oauth')) != 1:
            raise ValueError('Use oauth_enforce_username with exactly one oauth provider.')
        if val := os.environ.get('MARV_LEAVES_PATH'):
            values['leavesdir'] = val
        if val := os.environ.get('MARV_REVERSE_PROXY'):
            values['reverse_proxy'] = val
        if val := os.environ.get('MARV_VENV_PATH'):
            values['venv'] = val
        if val := os.environ.get('MARV_LEAFBIN_PATH'):
            values['leafbinpath'] = val
        else:
            values['leafbinpath'] = values['sitedir']
        return values


ParsedSexp = Tuple[str, Tuple[Any, ...]]


class CollectionConfig(Model):
    sitedir: Path  # TODO: workaround
    scanner: str
    scanroots: Tuple[Path, ...]
    compare: Optional[str] = None
    detail_summary_widgets: Tuple[str, ...] = """
    summary_keyval
    meta_table
    """
    detail_sections: Tuple[str, ...] = ''
    detail_title: ParsedSexp = '(get "dataset.name")'
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

    _parse_func = reapvalidator('detail_title')(parse_function)
    _strip = reapvalidator('scanner')(strip)
    _splitlines = reapvalidator('detail_sections', 'detail_summary_widgets', 'filters',
                                'listing_columns', 'listing_summary', 'nodes')(splitlines)
    _splitlines_relto_site = reapvalidator('scanroots')(splitlines_relto_site)
    _splitpipe = reapvalidator('listing_sort')(splitpipe)


class Config(Model):
    filename: Path
    marv: MarvConfig
    collections: Dict[str, CollectionConfig]

    _resolve_path = reapvalidator('filename')(resolve_path)

    @validator('collections')
    def collections_missing(cls, val, values):
        if 'marv' not in values:
            raise ValueError('Marv section could not be parsed')
        if missing := set(values['marv'].collections) - val.keys():
            raise ValueError(f'Collection section could not be parsed for {sorted(missing)}')
        return val

    @classmethod
    def from_file(cls, path):
        parser = ConfigParser()
        with path.open() as f:
            parser.read_file(f)
        return cls.from_parser(path, parser)

    @classmethod
    def from_parser(cls, path, parser):
        dct = {
            'collections': {},
            'filename': path,
        }
        for name, section in parser._sections.items():  # pylint: disable=protected-access
            section['sitedir'] = str(Path(path).resolve().parent)
            if name.startswith('collection'):
                dct['collections'][name.split(None, 1)[1]] = section
            else:
                dct[name] = section
        try:
            return cls.parse_obj(dct)
        except ValidationError as exc:
            raise ConfigError(str(exc))
