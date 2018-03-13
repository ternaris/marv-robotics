# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import functools
import inspect
import json
import os
import shutil
import tempfile
import unittest
import warnings
from collections import namedtuple
from contextlib import contextmanager
from logging import getLogger
from marv_cli import create_loglevels

create_loglevels()
warnings.simplefilter('always', DeprecationWarning)

from marv_node import run as marv_node_run
marv_node_run.RAISE_IF_UNFINISHED
marv_node_run.RAISE_IF_UNFINISHED = True

#from . import marv
from ..io import get_logger as marv_get_logger
from ..io import get_stream as marv_get_stream
from ..io import pull as marv_pull
from ..node import node as marv_node
from ..run import run_nodes  # export via testing
from ..setid import SetID


StubDataset = namedtuple('StubDataset', 'setid name collection files time_added timestamp')
StubFile = namedtuple('StubFile', 'idx path missing mtime size')


KEEP = os.environ.get('KEEP')
log = getLogger(__name__)


@contextmanager
def temporary_directory(keep=KEEP):
    """Create and cleanup temporary directory"""
    tmpdir = tempfile.mkdtemp()
    log.debug('created temporary directory %r', tmpdir)
    try:
        yield tmpdir
    finally:
        if not keep:
            shutil.rmtree(tmpdir)
            log.debug('cleaned up temporary directory %r', tmpdir)
        else:
            log.debug('keeping temporary directory %r by request', tmpdir)


def make_dataset(files=None, setid=None, name=None, collection=None,
                 time_added=None, timestamp=None):
    setid = SetID(42) if setid is None else setid
    name = 'NAME' if name is None else name
    collection = 'COL' if collection is None else collection
    files = [StubFile(i, x, False, 42, os.stat(x).st_size)
             for i, x in enumerate([] if files is None else files)]
    time_added = 0 if time_added is None else time_added
    timestamp = 0 if timestamp is None else timestamp
    return StubDataset(setid=setid, name=name, collection=collection,
                       files=files, time_added=time_added,
                       timestamp=timestamp)


def make_sink(node):
    msgs = []

    @marv_node()
    def testsink():
        log = yield marv_get_logger()
        stream = yield marv_get_stream(node)
        log.debug('recv %r', stream)

        while True:
            msg = yield marv_pull(stream)
            log.debug('recv %r', msg)
            if msg is None:
                return
            msgs.append(msg)

    testsink._key = '{}-testsink'.format(node.abbrev)
    testsink.stream = msgs
    return testsink


class Spy(object):
    def __init__(self):
        self.requests = []


def make_spy(node):
    spy = Spy()
    requests = spy.requests
    real_invoke = node.invoke
    @functools.wraps(real_invoke)
    def invoke(inputs=None):
        gen = real_invoke(inputs)
        req = gen.next()
        while True:
            requests.append(req)
            send = yield req
            req = gen.send(send)
    node.invoke = invoke
    return spy


class TestCase(unittest.TestCase):
    BAGS = None
    MARV_TESTING_RECORD = os.environ.get('MARV_TESTING_RECORD')
    bags = None
    cleanup = None
    maxDiff = None
    scanroot = None

    @classmethod
    def setUpClass(cls):
        scanroot = tempfile.mkdtemp()
        @classmethod
        def cleanup(cls):
            shutil.rmtree(scanroot)
        cls.cleanup_class = cleanup

    @classmethod
    def tearDownClass(cls):
        cls.cleanup_class()

    def assertNodeOutput(self, output, node):
        name = node.name
        testfile = inspect.getmodule(type(self)).__file__
        dirpath = os.path.join(os.path.dirname(testfile), 'output')
        if not os.path.isdir(dirpath):
            os.mkdir(dirpath)
        outfile = os.path.join(dirpath, name + '.json')
        out = [x.to_dict(verbose=True, which=True) for x in output]
        if self.MARV_TESTING_RECORD:
            with open(outfile, 'w') as f:
                json.dump(out, f, sort_keys=True, indent=2)
        else:
            with open(outfile) as f:
                self.assertEqual(json.loads(json.dumps(out)), json.load(f))
