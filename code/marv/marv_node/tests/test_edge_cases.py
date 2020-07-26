# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=invalid-name

from ..testing import make_dataset, marv, run_nodes

DATASET = make_dataset()
SETID = DATASET.setid


@marv.node(group=True)
def source():
    a = yield marv.create_stream('a')
    b = yield marv.create_stream('b')
    yield a.msg(0)
    yield b.msg(10)


@marv.node()
@marv.input('stream', foreach=source)
def images(stream):
    """Produce 2 streams each with 5 messages."""
    offset = yield marv.pull(stream)
    yield marv.set_header(title=offset)
    yield marv.push(1 + offset)
    yield marv.push(2 + offset)
    yield marv.push(3 + offset)
    yield marv.push(4 + offset)
    yield marv.push(5 + offset)


@marv.node()
@marv.input('stream', foreach=images)
def galleries(stream):
    """Consume each stream into a list."""
    yield marv.set_header(title=stream.title)  # TODO: This is currently needed
    _images = []
    while True:
        img = yield marv.pull(stream)
        if img is None:
            break
        _images.append(img)
    yield marv.push({'images': _images})


@marv.node()
@marv.input('galleries', default=galleries)
def images_section(galleries):  # pylint: disable=redefined-outer-name
    """Consume both galleries into a list."""
    tmp = []
    while True:
        msg = yield marv.pull(galleries)
        if msg is None:
            break
        tmp.append(msg)
    galleries = tmp
    galleries = yield marv.pull_all(*galleries)
    yield marv.push({'galleries': galleries})


async def test_foreach_cascade():
    nodes = [images_section]
    streams = await run_nodes(DATASET, nodes)
    assert streams == [
        [{'galleries': [
            {'images': [1, 2, 3, 4, 5]},
            {'images': [11, 12, 13, 14, 15]},
        ]}],
    ]
