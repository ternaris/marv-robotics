# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import logging

from testfixtures import LogCapture

from ..testing import make_dataset, marv, run_nodes

DATASET = make_dataset()


@marv.node(group=True)
def source():
    yield marv.create_stream('Output 1')
    yield marv.create_stream('Output 2', foo=1)


@marv.node()
@marv.input('source', source)
def consumer(source):  # pylint: disable=redefined-outer-name
    logger = yield marv.get_logger()
    stream = yield marv.pull(source)
    logger.critical((stream.name, stream.header))
    stream = yield marv.pull(source)
    logger.critical((stream.name, stream.header))


async def test():
    with LogCapture(level=logging.CRITICAL) as log:
        await run_nodes(DATASET, [consumer])

    assert [x.msg for x in log.records if x.msg] == [
        ('Output 1', {}),
        ('Output 2', {'foo': 1}),
    ]
