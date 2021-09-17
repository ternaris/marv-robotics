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
    all_msgs = {'a': list(range(1)), 'b': list(range(2)), 'c': list(range(3))}
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
def node_a(a):
    yield marv.set_header(topic='a')
    while True:
        msg = yield marv.pull(a)
        if msg is None:
            return
        yield marv.push(f'node_a-{msg}')


@marv.node()
@marv.input('b', default=marv.select(messages, 'b'))
def node_b(b):
    yield marv.set_header(topic='b')
    while True:
        msg = yield marv.pull(b)
        if msg is None:
            return
        yield marv.push(f'node_b-{msg}')


@marv.node()
@marv.input('c', default=marv.select(messages, 'c'))
def node_c(c):
    yield marv.set_header(topic='c')
    while True:
        msg = yield marv.pull(c)
        if msg is None:
            return
        yield marv.push(f'node_c-{msg}')


@marv.node()
@marv.input('node_a', default=node_a)
@marv.input('node_b', default=node_b)
@marv.input('node_c', default=node_c)
def collect(node_a, node_b, node_c):
    yield marv.set_header()
    acc = []
    streams = [node_a, node_b, node_c]
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
        [{
            'acc': ['node_b-b0', 'node_c-c0', 'node_b-b1', 'node_c-c1', 'node_c-c2'],
        }],
    ]
