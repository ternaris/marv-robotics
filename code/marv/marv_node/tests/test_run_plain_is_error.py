# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import pytest

from ..testing import make_dataset, marv, run_nodes


@marv.node()
def source():
    yield 1


DATASET = make_dataset()


async def test():
    nodes = [source]
    with pytest.raises(RuntimeError):  # TODO: proper exception
        await run_nodes(DATASET, nodes)
