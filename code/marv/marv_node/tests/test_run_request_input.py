# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import logging

from testfixtures import LogCapture

from ..testing import make_dataset, marv, run_nodes

DATASET = make_dataset()
SETID = DATASET.setid


@marv.node(group=True)
def multi():
    logger = yield marv.get_logger()
    logger.critical('multi started')
    a_out = yield marv.create_stream('a')
    b_out = yield marv.create_stream('b')
    assert a_out.name == 'a'
    assert b_out.name == 'b'

    yield a_out.msg(1)
    yield b_out.msg(10)
    yield a_out.msg(2)
    yield b_out.msg(20)
    logger.critical('multi finished')


@marv.node()
@marv.input('node', default=multi)
def consumer(node):
    logger = yield marv.get_logger()
    logger.critical('consumer started')
    a_in, b_in = yield marv.pull_all(node, node)
    assert a_in.name == 'a'
    assert b_in.name == 'b'
    # streams = yield marv.io(*node)  # like for values
    # streams = yield marv.io(node, consume=True)  # a bit less voodoo

    values = []
    while True:
        msgs = yield marv.pull_all(a_in, b_in)
        if msgs == [None, None]:
            break
        values.append(msgs)
    assert values == [[1, 10], [2, 20]]
    logger.critical('consumer finished')


async def test():
    nodes = [consumer]
    with LogCapture(level=logging.CRITICAL) as log:
        await run_nodes(DATASET, nodes)

    assert [x.msg for x in log.records] == [
        'multi started',
        'consumer started',
        'multi finished',
        'consumer finished',
    ]
