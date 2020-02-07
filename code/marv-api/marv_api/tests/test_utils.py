# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=too-few-public-methods

from .. import utils


def test_notset():
    assert repr(utils.NOTSET) == '<NOTSET>'
    assert isinstance(utils.NOTSET, tuple)
    empty_tuple = ()
    assert utils.NOTSET is not empty_tuple
