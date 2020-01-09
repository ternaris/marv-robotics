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
    yield out1.msg(a=1)
    yield out1.msg(a=2)


@marv.node()
@marv.input('stream', foreach=source)
def foreach(stream):
    yield marv.set_header(**stream.header)
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        msg = yield marv.push(msg)


@marv.node()
@marv.input('foreaches', default=foreach)
def consumer(foreaches):
    logger = yield marv.get_logger()
    while True:
        stream = yield marv.pull(foreaches)
        if stream is None:
            break
        logger.critical((stream.name, stream.header))
        while True:
            msg = yield marv.pull(stream)
            if msg is None:
                break
            logger.critical(msg)


async def test():
    with LogCapture(level=logging.CRITICAL) as log:
        await run_nodes(DATASET, [consumer])

    assert [x.msg for x in log.records if x.msg] == [
        ('0', {'foo': 1}),
        {'a': 1},
        {'a': 2},
    ]
