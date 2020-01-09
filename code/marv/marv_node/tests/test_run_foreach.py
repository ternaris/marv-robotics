# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import logging

from testfixtures import LogCapture

from ..testing import make_dataset, marv, run_nodes

DATASET = make_dataset()
SETID = DATASET.setid


@marv.node(group=True)
def source():
    out1 = yield marv.create_stream('Output 1', foo=1)
    out2 = yield marv.create_stream('Output 2', foo=2)
    out3 = yield marv.create_stream('Output 3', foo=3)
    yield out1.msg(a=1)
    yield out2.msg(b=10)
    yield out3.msg(c=100)
    yield out1.msg(a=2)
    yield out2.msg(b=20)
    yield out3.msg(c=200)


@marv.node()
@marv.input('stream', foreach=source)
def foreach(stream):
    logger = yield marv.get_logger()
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        logger.critical((0, stream.name, msg))


@marv.node()
@marv.input('node', default=source)
def withall(node):
    logger = yield marv.get_logger()
    streams = []
    while True:
        stream = yield marv.pull(node)
        if stream is None:
            break
        streams.append(stream)

    while streams:
        msgs = yield marv.pull_all(*streams)
        logger.critical((1, msgs))
        streams = [stream for stream, msg in zip(streams, msgs) if msg is not None]


async def test():
    with LogCapture(level=logging.CRITICAL) as log:
        await run_nodes(DATASET, [foreach, withall])

    assert [x.msg for x in log.records if x.msg[0] == 0] == [
        (0, 'Output 1', {'a': 1}),
        (0, 'Output 2', {'b': 10}),
        (0, 'Output 3', {'c': 100}),
        (0, 'Output 1', {'a': 2}),
        (0, 'Output 2', {'b': 20}),
        (0, 'Output 3', {'c': 200}),
    ]
    assert [x.msg for x in log.records if x.msg[0] == 1] == [
        (1, [{'a': 1}, {'b': 10}, {'c': 100}]),
        (1, [{'a': 2}, {'b': 20}, {'c': 200}]),
        (1, [None, None, None]),
    ]
