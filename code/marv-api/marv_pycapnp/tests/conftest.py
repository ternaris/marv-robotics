# Copyright 2016 - 2021  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import pytest


@pytest.fixture
def tmpdir(tmp_path):
    """We don't want pytest's path implementation."""
    return tmp_path
