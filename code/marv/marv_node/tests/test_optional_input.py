# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=invalid-name,redefined-outer-name

from ..testing import make_dataset, marv, run_nodes

DATASET = make_dataset()
SETID = DATASET.setid


@marv.node()
def meta():
    """Meta information about a dataset."""
    yield marv.push({'topics': ['b', 'c']})


@marv.node(group='ondemand')
@marv.input('meta', default=meta)
def messages(meta):
    """Produce streams for requested topics if they exist."""
    meta = yield marv.pull(meta)
    requested = yield marv.get_requested()
    all_msgs = {'a': list(range(1)),
                'b': list(range(2)),
                'c': list(range(3))}
    topics = [x.name for x in requested]
    streams = {}
    for topic in topics:
        stream = yield marv.create_stream(topic)
        if topic in meta['topics']:
            streams[topic] = stream
        else:
            yield stream.finish()

    while streams:
        for topic, stream in list(streams.items()):
            msgs = all_msgs[topic]
            msg = msgs.pop(0)
            yield stream.msg(f'{topic}{msg}')
            if not msgs:
                del streams[topic]


@marv.node()
@marv.input('a', default=marv.select(messages, 'a'))
def nodeA(a):
    yield marv.set_header(topic='a')
    while True:
        msg = yield marv.pull(a)
        if msg is None:
            return
        yield marv.push(f'nodeA-{msg}')


@marv.node()
@marv.input('b', default=marv.select(messages, 'b'))
def nodeB(b):
    yield marv.set_header(topic='b')
    while True:
        msg = yield marv.pull(b)
        if msg is None:
            return
        yield marv.push(f'nodeB-{msg}')


@marv.node()
@marv.input('c', default=marv.select(messages, 'c'))
def nodeC(c):
    yield marv.set_header(topic='c')
    while True:
        msg = yield marv.pull(c)
        if msg is None:
            return
        yield marv.push(f'nodeC-{msg}')


@marv.node()
@marv.input('nodeA', default=nodeA)
@marv.input('nodeB', default=nodeB)
@marv.input('nodeC', default=nodeC)
def collect(nodeA, nodeB, nodeC):
    yield marv.set_header()
    acc = []
    streams = [nodeA, nodeB, nodeC]
    while streams:
        for stream in streams[:]:
            msg = yield marv.pull(stream)
            if msg is None:
                streams.remove(stream)
                continue
            acc.append(msg)
    yield marv.push({'acc': acc})


async def test():
    nodes = [collect]
    streams = await run_nodes(DATASET, nodes)
    assert streams == [
        [{'acc': ['nodeB-b0', 'nodeC-c0', 'nodeB-b1', 'nodeC-c1', 'nodeC-c2']}],
    ]
