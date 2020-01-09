# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import logging
from itertools import product

from testfixtures import LogCapture

from ..testing import make_dataset, marv, run_nodes

DATASET = make_dataset()
SETID = DATASET.setid


@marv.node(group='ondemand')
def source():
    logger = yield marv.get_logger()
    requested = yield marv.get_requested()
    logger.critical([x.name for x in requested])
    creates = [marv.create_stream(x.name) for x in requested]
    streams = []
    for create in creates:
        stream = yield create
        streams.append(stream)
    msgs = list(product(streams, [1, 2]))
    for stream, msg in msgs:
        yield marv.push(stream.msg(msg))


@marv.node()
def stream_a():
    stream = yield marv.get_stream(source, 'a')
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        msg = yield marv.push(msg)


@marv.node()
def stream_b():
    stream = yield marv.get_stream(source, 'b')
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        msg = yield marv.push(msg)


@marv.node(group=True)
def merged():
    stream1 = yield marv.get_stream(stream_a)
    stream2 = yield marv.get_stream(stream_b)
    yield marv.push(stream1)
    yield marv.push(stream2)


@marv.node()
@marv.input('stream', foreach=merged)
def consumer(stream):
    logger = yield marv.get_logger()
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        logger.critical((stream.node.name, stream.name, msg))


async def test():
    nodes = [consumer]
    await run_nodes(DATASET, nodes)

    with LogCapture(level=logging.CRITICAL) as log:
        await run_nodes(DATASET, nodes)

    assert [x.msg for x in log.records] == [
        ['a'],
        ['a', 'b'],
        ('stream_a', 'default', 1),
        ('stream_a', 'default', 2),
        ('stream_b', 'default', 1),
        ('stream_b', 'default', 2),
    ]
