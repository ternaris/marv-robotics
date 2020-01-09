# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import logging

from testfixtures import LogCapture

from ..run import run_nodes
from ..testing import make_dataset, marv

DATASET = make_dataset()
SETID = DATASET.setid


@marv.node(group=True)
def source():
    out1 = yield marv.create_stream('Output 1')
    out2 = yield marv.create_stream('Output 2')
    out3 = yield marv.create_stream('Output 3')
    yield out1.msg(a=1)
    yield out2.msg(b=10)
    yield out3.msg(c=100)
    yield out1.msg(a=2)
    yield out2.msg(b=20)
    yield out3.msg(c=200)


@marv.node(group=True)
def forking(stream=None):
    logger = yield marv.get_logger()
    node = yield marv.get_stream(source)  # UX not nice, naming

    if stream is None:
        stream = yield marv.pull(node)
        other = yield marv.pull(node)
        while other is not None:
            name = other.key[-1]
            yield marv.fork(name, inputs={'stream': other}, group=False)
            other = yield marv.pull(node)

    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        logger.critical((stream.key, msg))


async def test():
    with LogCapture(level=logging.CRITICAL) as log:
        await run_nodes(DATASET, [forking], {})

    assert [x.msg for x in log.records] == [
        ((SETID, source, 'Output 2'), {'b': 10}),
        ((SETID, source, 'Output 3'), {'c': 100}),
        ((SETID, source, 'Output 2'), {'b': 20}),
        ((SETID, source, 'Output 3'), {'c': 200}),
        ((SETID, source, 'Output 1'), {'a': 1}),
        ((SETID, source, 'Output 1'), {'a': 2}),
    ]
