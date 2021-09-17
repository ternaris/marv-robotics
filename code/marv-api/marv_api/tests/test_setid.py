# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import unittest

from ..setid import SetID, decode_setid, encode_setid


class TestCase(unittest.TestCase):

    def test_setid(self):  # pylint: disable=no-self-use
        assert SetID(42) != SetID(17)
        assert SetID(42) == SetID('fiaaaaaaaaaaaaaaaaaaaaaaaa')
        assert repr(SetID(42)) == "SetID('fiaaaaaaaaaaaaaaaaaaaaaaaa')"
        assert str(SetID(42)) == 'fiaaaaaaaaaaaaaaaaaaaaaaaa'
        setid = SetID(42)
        assert setid.lohi == (setid.lo, setid.hi)
        assert setid.lohi == (42, 0)
        assert int(setid) == 42
        assert SetID(42, 0) == SetID(42)
        assert SetID(42, 1) == SetID((1 << 64) + 42)

    def test_encode_decode_setid(self):  # pylint: disable=no-self-use
        setid = 2**128 - 1
        encoded = encode_setid(setid)
        decoded = decode_setid(encoded.lower())
        assert encoded == '77777777777777777777777774'
        assert decoded == setid
