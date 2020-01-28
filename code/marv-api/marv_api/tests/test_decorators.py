# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import pytest

import marv_api as marv


def test_node_duplicate_input():
    with pytest.raises(marv.InputNameCollision):
        @marv.node()
        @marv.input('a')
        @marv.input('a')
        def collision():  # pylint: disable=unused-variable
            yield
