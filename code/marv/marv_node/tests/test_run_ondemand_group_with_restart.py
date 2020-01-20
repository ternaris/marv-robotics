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
@marv.input('stream1', default=marv.select(source, 'a'))
@marv.input('stream2', default=marv.select(source, 'b'))
def consumer(stream1, stream2):
    streams = [stream1, stream2]
    while streams:
        for stream in streams[:]:
            msg = yield marv.pull(stream)
            if msg is None:
                streams.remove(stream)
                continue
            yield marv.push((stream.name, msg))


async def test():
    nodes = [consumer]

    with LogCapture(level=logging.CRITICAL) as log:
        streams = await run_nodes(DATASET, nodes)

    assert [x.msg for x in log.records] == [
        ['b'],
        ['a', 'b'],
    ]
    assert streams == [
        [('a', 1), ('b', 1), ('a', 2), ('b', 2)],
    ]
