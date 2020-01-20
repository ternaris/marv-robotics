# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from ..testing import make_dataset, marv, run_nodes

DATASET = make_dataset()
SETID = DATASET.setid


@marv.node(group='ondemand')
def source():
    requested = yield marv.get_requested()
    assert {x.name for x in requested} == {'evensub', 'oddsub', 'primesub'}

    out = {x.name: marv.create_stream(x.name) for x in requested}
    for key, stream in out.items():
        out[key] = yield stream
    assert out.keys() == {'evensub', 'oddsub', 'primesub'}

    for idx in range(1, 6):
        yield marv.push(out['oddsub' if idx % 2 else 'evensub'].msg(idx))
        if idx in [2, 3, 5]:
            yield marv.push(out['primesub'].msg(idx))

    # How do we output one message for multiple streams?


@marv.node()
@marv.input('stream', default=marv.select(source, 'evensub'))
def even(stream):
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        msg = yield marv.push(msg)


@marv.node()
@marv.input('stream', default=marv.select(source, 'oddsub'))
def odd(stream):
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        msg = yield marv.push(msg)


@marv.node()
@marv.input('stream', default=marv.select(source, 'primesub'))
def prime(stream):
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        msg = yield marv.push(msg)


async def test():
    nodes = [even, odd, prime]
    streams = await run_nodes(DATASET, nodes)
    assert streams == [
        [2, 4],
        [1, 3, 5],
        [2, 3, 5],
    ]
