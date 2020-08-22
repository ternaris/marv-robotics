# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import functools
import inspect
import json
import os
import shutil
import tempfile
from collections import namedtuple
from contextlib import contextmanager
from logging import getLogger

import marv_api as marv  # pylint: disable=unused-import
from marv_api.setid import SetID
from marv_cli import create_loglevels
from marv_node import run as marv_node_run
from marv_node.node import Node

from ..run import run_nodes as _run_nodes

create_loglevels()

marv_node_run.RAISE_IF_UNFINISHED = True

StubDataset = namedtuple('StubDataset', 'setid name collection files time_added timestamp')
StubFile = namedtuple('StubFile', 'idx path missing mtime size')

KEEP = os.environ.get('KEEP')
LOG = getLogger(__name__)


@contextmanager
def temporary_directory(keep=KEEP):
    """Create and cleanup temporary directory."""
    tmpdir = tempfile.mkdtemp()
    LOG.debug('created temporary directory %r', tmpdir)
    try:
        yield tmpdir
    finally:
        if not keep:
            shutil.rmtree(tmpdir)
            LOG.debug('cleaned up temporary directory %r', tmpdir)
        else:
            LOG.debug('keeping temporary directory %r by request', tmpdir)


def make_dataset(files=None, setid=None, name=None, collection=None,
                 time_added=None, timestamp=None):
    # pylint: disable=too-many-arguments
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


async def run_nodes(dataset, nodes, store=None, persistent=None, **kw):
    """Wrap marv_node.run.run_nodes gathering streams for provided nodes."""
    nodes = [x if isinstance(x, Node) else Node.from_dag_node(x) for x in nodes]
    persistent = {
        k: v if isinstance(v, Node) else Node.from_dag_node(v)
        for k, v in (persistent or {}).items()
    }
    streams = {}
    await _run_nodes(dataset,
                     nodes,
                     {} if store is None else store,
                     persistent=persistent,
                     _gather_into=streams,
                     **kw)
    return [streams.get(x) for x in nodes]


class Spy:  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.requests = []


def make_spy(node):
    spy = Spy()
    requests = spy.requests
    real_invoke = node.invoke

    @functools.wraps(real_invoke)
    def invoke(inputs=None):
        gen = real_invoke(inputs)
        try:
            req = next(gen)
        except StopIteration:
            return

        while True:
            requests.append(req)
            send = yield req
            try:
                req = gen.send(send)
            except StopIteration:
                return

    node.invoke = invoke
    return spy


class TestCase:  # pylint: disable=too-few-public-methods
    BAGS = None
    MARV_TESTING_RECORD = os.environ.get('MARV_TESTING_RECORD')

    def assertNodeOutput(self, output, node):  # pylint: disable=invalid-name
        name = node.__marv_node__.function.rsplit('.', 1)[1]
        testfile = inspect.getmodule(type(self)).__file__
        dirpath = os.path.join(os.path.dirname(testfile), 'output')
        if not os.path.isdir(dirpath):
            os.mkdir(dirpath)
        outfile = os.path.join(dirpath, name + '.json')
        out = [x.to_dict(which=True) for x in output]
        if self.MARV_TESTING_RECORD:
            with open(outfile, 'w') as f:
                json.dump(out, f, sort_keys=True, indent=2)
        else:
            with open(outfile) as f:
                assert json.loads(json.dumps(out)) == json.load(f)
