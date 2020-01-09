# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=invalid-name

from ..testing import make_dataset, marv, run_nodes


@marv.node()
@marv.input('offset', default=0)
def root(offset):
    yield marv.push(10+offset)
    yield marv.push(20+offset)


@marv.node()
@marv.input('stream_a', default=root)
def square(stream_a):
    while True:
        a = yield marv.pull(stream_a)
        if a is None:
            break
        yield marv.push(a**2)


@marv.node()
@marv.input('stream_a', default=root)
@marv.input('stream_b', default=root.clone(offset=5))
@marv.input('stream_c', default=square)
def add(stream_a, stream_b, stream_c):
    while True:
        a, b, c = yield marv.pull_all(stream_a, stream_b, stream_c)
        if a is None:
            break
        yield marv.push(a+b+c)


DATASET = make_dataset()


async def test():
    nodes = [root, square, add]
    streams = await run_nodes(DATASET, nodes)
    assert streams == [
        [10, 20],
        [100, 400],
        [125, 445],
    ]
