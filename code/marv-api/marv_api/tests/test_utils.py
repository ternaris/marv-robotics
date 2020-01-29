# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=too-few-public-methods

import pytest

from .. import utils


def test_notset():
    assert repr(utils.NOTSET) == '<NOTSET>'
    assert isinstance(utils.NOTSET, tuple)
    empty_tuple = ()
    assert utils.NOTSET is not empty_tuple


def test_popattr():
    class Foo:
        a = 1
        bb = 2

    assert utils.popattr(Foo, 'a') == 1
    with pytest.raises(AttributeError):
        assert utils.popattr(Foo, 'a')
    assert utils.popattr(Foo, 'a', None) is None
    assert utils.popattr(Foo, 'bb', None) == 2
    assert utils.popattr(Foo, 'bb', None) is None


def test_exclusive_setitem():
    dct = {}
    utils.exclusive_setitem(dct, 'foo', 1)
    assert dct['foo'] == 1
    with pytest.raises(KeyError):
        utils.exclusive_setitem(dct, 'foo', 1)
    with pytest.raises(ValueError):
        utils.exclusive_setitem(dct, 'foo', 1, ValueError)
