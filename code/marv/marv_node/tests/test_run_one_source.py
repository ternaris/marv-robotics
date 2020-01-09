# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from ..testing import make_dataset, marv, run_nodes


@marv.node()
def source():
    yield marv.push(1)
    yield marv.push(2)
    yield marv.push(3)


DATASET = make_dataset()


async def test():
    nodes = [source]
    streams = await run_nodes(DATASET, nodes)
    assert streams == [
        [1, 2, 3],
    ]
