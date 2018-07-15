# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

from collections import defaultdict
from itertools import product

from ..testing import make_dataset, make_sink, marv

from ..run import run_nodes
from ..stream import Handle


dataset = make_dataset()
SETID = dataset.setid


@marv.node()
def meta():
    """Meta information about a dataset"""
    yield marv.push({'topics': ['b', 'c']})


@marv.node(group='ondemand')
@marv.input('meta', default=meta)
def messages(meta):
    """Produce streams for requested topics if they exist"""
    meta = yield marv.pull(meta)
    requested = yield marv.get_requested()
    all_msgs = {'a': range(1),
                'b': range(2),
                'c': range(3)}
    topics = [x.name for x in requested]
    streams = {}
    for topic in topics:
        stream = yield marv.create_stream(topic)
        if topic in meta['topics']:
            streams[topic] = stream
        else:
            yield stream.finish()

    while streams:
        for topic, stream in streams.items():
            msgs = all_msgs[topic]
            msg = msgs.pop(0)
            yield stream.msg('{}{}'.format(topic, msg))
            if not msgs:
                del streams[topic]


@marv.node()
@marv.input('a', default=marv.select(messages, 'a'))
def nodeA(a):
    yield marv.set_header(topic='a')
    while True:
        msg = yield marv.pull(a)
        if msg is None:
            return
        yield marv.push('nodeA-{}'.format(msg))


@marv.node()
@marv.input('b', default=marv.select(messages, 'b'))
def nodeB(b):
    yield marv.set_header(topic='b')
    while True:
        msg = yield marv.pull(b)
        if msg is None:
            return
        yield marv.push('nodeB-{}'.format(msg))


@marv.node()
@marv.input('c', default=marv.select(messages, 'c'))
def nodeC(c):
    yield marv.set_header(topic='c')
    while True:
        msg = yield marv.pull(c)
        if msg is None:
            return
        yield marv.push('nodeC-{}'.format(msg))


@marv.node()
@marv.input('nodeA', default=nodeA)
@marv.input('nodeB', default=nodeB)
@marv.input('nodeC', default=nodeC)
def collect(nodeA, nodeB, nodeC):
    yield marv.set_header()
    acc = []
    streams = [nodeA, nodeB, nodeC]
    while streams:
        for stream in streams[:]:
            msg = yield marv.pull(stream)
            if msg is None:
                streams.remove(stream)
                continue
            acc.append(msg)
    yield marv.push({'acc': acc})


def test():
    sink = make_sink(collect)
    run_nodes(dataset, [sink], {})
    assert sink.stream == [{'acc': ['nodeB-b0', 'nodeC-c0', 'nodeB-b1', 'nodeC-c1', 'nodeC-c2']}]
