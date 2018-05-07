# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

__version__ = '3.3.5'

import logging
import os

import click
from collections import OrderedDict
from pkg_resources import iter_entry_points


FORMAT = os.environ.get('MARV_LOG_FORMAT',
                        '%(asctime)s %(levelname).4s %(name)s %(message)s')
IPDB = False

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


def make_log_method(name, numeric):
    upper = name.upper()
    assert not hasattr(logging, upper)
    setattr(logging, upper, numeric)

    def method(self, msg, *args, **kw):
        if self.isEnabledFor(numeric):
            self._log(numeric, msg, args, **kw)
    method.__name__ = name
    return method


def create_loglevels():
    cls = logging.getLoggerClass()
    for k, v in LOGLEVEL.items():
        if not hasattr(cls, k):
            logging.addLevelName(v, k.upper())
            method = make_log_method(k, v)
            setattr(cls, k, method)
create_loglevels()


def setup_logging(loglevel, verbosity=0, logfilter=None):
    create_loglevels()

    class Filter(logging.Filter):
        def filter(self, record):
            if logfilter and not any(record.name.startswith(x) for x in logfilter):
                return False
            if record.name == 'rospy.core' and \
               record.msg == 'signal_shutdown [atexit]':
                return False
            return True
    filter = Filter()

    formatter = logging.Formatter(FORMAT)
    handler = logging.StreamHandler()
    handler.addFilter(filter)
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.addHandler(handler)

    levels = LOGLEVEL.keys()
    level = levels[min(levels.index(loglevel) + verbosity, len(levels) - 1)]
    root.setLevel(LOGLEVEL[level])

    if os.environ.get('MARV_ECHO_SQL'):
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


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
@click.pass_context
def marv(ctx, config, loglevel, logfilter, verbosity):
    """Manage a Marv site"""
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
    ctx.obj = config
    setup_logging(loglevel, verbosity, logfilter)


def cli():
    """setuptools entry_point"""
    for ep in iter_entry_points(group='marv_cli'):
        ep.load()
    marv(auto_envvar_prefix='MARV')


def cli_ipdb():
    global IPDB
    IPDB = True
    from ipdb import launch_ipdb_on_exception
    with launch_ipdb_on_exception():
        cli()


if __name__ == '__main__':
    cli()
