# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import logging
import os
from collections import OrderedDict
from contextlib import contextmanager
from pathlib import Path

import click
from pkg_resources import iter_entry_points

try:
    import marv_ee
except ImportError:
    marv_ee = None

if marv_ee:
    marv_ee.init()
    from marv_ee import VERSION_MESSAGE, copying_option  # pylint: disable=import-error
else:
    VERSION_MESSAGE = """
%(prog)s (MARV Community Edition) %(version)s
Copyright (C) 2016 - 2021  Ternaris and the MARV Contributors.
License AGPL-3.0-only: GNU Affero General Public License v3.0 <https://spdx.org/licenses/AGPL-3.0.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
""".strip()

    def copying_option(func):
        return func


FORMAT = os.environ.get('MARV_LOG_FORMAT', '%(asctime)s %(levelname).4s %(name)s %(message)s')
PDB = None
STATICX_PROG_PATH = os.environ.get('STATICX_PROG_PATH')

# needs to be in line with logging
LOGLEVEL = OrderedDict((
    ('critical', 50),
    ('error', 40),
    ('warning', 30),
    ('info', 20),
    ('verbose', 18),
    ('noisy', 15),
    ('debug', 10),
))


# TODO: duplicated from marv_api.utils
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


def make_log_method(name, numeric):
    upper = name.upper()
    assert not hasattr(logging, upper)
    setattr(logging, upper, numeric)

    def method(self, msg, *args, **kw):
        if self.isEnabledFor(numeric):
            self._log(numeric, msg, args, **kw)  # pylint: disable=protected-access
    method.__name__ = name
    return method


def create_loglevels():
    cls = logging.getLoggerClass()
    for name, value in LOGLEVEL.items():
        if not hasattr(cls, name):
            logging.addLevelName(value, name.upper())
            method = make_log_method(name, value)
            setattr(cls, name, method)


create_loglevels()


def setup_logging(loglevel, verbosity=0, logfilter=None):
    create_loglevels()

    class Filter(logging.Filter):  # pylint: disable=too-few-public-methods
        def filter(self, record):
            if logfilter and not any(record.name.startswith(x) for x in logfilter):
                return False
            if record.name == 'aiosqlite' and 'returning exception' in record.msg:
                return False
            return True
    filter = Filter()

    formatter = logging.Formatter(FORMAT)
    handler = logging.StreamHandler()
    handler.addFilter(filter)
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.addHandler(handler)

    levels = list(LOGLEVEL.keys())
    level = levels[min(levels.index(loglevel) + verbosity, len(levels) - 1)]
    root.setLevel(LOGLEVEL[level])

    logging.getLogger('tortoise').setLevel(logging.INFO if os.environ.get('MARV_ECHO_SQL') else
                                           logging.WARN)


@click.group()
@click.option('--config',
              type=click.Path(dir_okay=False, exists=True, resolve_path=True),
              help='Path to config file'
              ' (default: 1. ./marv.conf, 2. /etc/marv/marv.conf)')
@click.option('--loglevel', default='info', show_default=True,
              type=click.Choice(LOGLEVEL.keys()),
              help='Set loglevel directly')
@click.option('--logfilter', multiple=True,
              help='Display only log messages for selected loggers')
@click.option('-v', '--verbose', 'verbosity', count=True,
              help='Increase verbosity beyond --loglevel')
@click.version_option(message=VERSION_MESSAGE)
@copying_option
@click.pass_context
def marv(ctx, config, loglevel, logfilter, verbosity):
    """Manage a Marv site."""
    if config is None:
        cwd = os.path.abspath(os.path.curdir)
        while cwd != os.path.sep:
            config = os.path.join(cwd, 'marv.conf')
            if os.path.exists(config):
                break
            cwd = os.path.dirname(cwd)
        else:
            config = '/etc/marv/marv.conf'
            if not os.path.exists(config):
                config = None
    if config is not None:
        ctx.obj = Path(config)
    setup_logging(loglevel, verbosity, logfilter)


def cli():
    """Setuptools entry_point."""
    ldpath = os.environ.get('LD_LIBRARY_PATH')
    if ldpath:
        os.environ['LD_LIBRARY_PATH'] = ':'.join(
            x
            for x in ldpath.split(':')
            if not x.startswith('/tmp/_MEI')
        )

    global PDB  # pylint: disable=global-statement
    PDB = bool(os.environ.get('PDB'))
    with launch_pdb_on_exception(PDB):
        for entry_point in iter_entry_points(group='marv_cli'):
            entry_point.load()
        prog_name = STATICX_PROG_PATH and Path(STATICX_PROG_PATH).name
        # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
        marv(auto_envvar_prefix='MARV', prog_name=prog_name)


if __name__ == '__main__':
    cli()
