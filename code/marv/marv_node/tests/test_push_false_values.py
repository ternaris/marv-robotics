# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=invalid-name

import pytest

from ..testing import make_dataset, marv, run_nodes


class Falsish:
    def __bool__(self):
        return False

    def __eq__(self, other):
        return type(other) is type(self)

    def __repr__(self):
        return '<FALSISH>'


FALSISH = Falsish()


class DontBoolMe:
    def __bool__(self):
        raise Exception

    def __eq__(self, other):
        return type(other) is type(self)

    def __repr__(self):
        return '<DONTBOOLME>'


DONTBOOLME = DontBoolMe()


@marv.node()
def source():
    # yield marv.push(None) -- So far, this means we're done
    yield marv.push(0)
    yield marv.push(0.0)
    yield marv.push(False)
    yield marv.push('')
    yield marv.push(FALSISH)
    yield marv.push(DONTBOOLME)


@marv.node()
@marv.input('stream', default=source)
def consumer1(stream):
    yield marv.push(42)
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        yield marv.push(msg)


@marv.node()
@marv.input('stream', default=source)
def consumer2(stream):
    yield marv.push(42)
    while True:
        msg, = yield marv.pull_all(stream)
        if msg is None:
            break
        yield marv.push(msg)


DATASET = make_dataset()


async def test():
    with pytest.raises(Exception):
        if DONTBOOLME:
            pass

    nodes = [source, consumer1, consumer2]
    streams = await run_nodes(DATASET, nodes)
    assert streams == [
        [0, 0.0, False, '', FALSISH, DONTBOOLME],
        [42, 0, 0.0, False, '', FALSISH, DONTBOOLME],
        [42, 0, 0.0, False, '', FALSISH, DONTBOOLME],
    ]
