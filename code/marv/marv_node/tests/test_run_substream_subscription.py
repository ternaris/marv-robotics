# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from ..testing import make_dataset, marv, run_nodes


@marv.node(group='ondemand')
def source():
    out = yield marv.create_stream('foo')
    yield out.msg(1)


@marv.node()
@marv.input('handle', default=marv.select(source, 'foo'))
def consumer(handle):
    while True:
        msg = yield marv.pull(handle)
        if msg is None:
            break
        yield marv.push(msg)


DATASET = make_dataset()


async def test():
    nodes = [consumer]
    streams = await run_nodes(DATASET, nodes)
    assert streams == [
        [1],
    ]
