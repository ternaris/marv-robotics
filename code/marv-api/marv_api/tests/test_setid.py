# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import unittest

from ..setid import SetID, decode_setid, encode_setid


class TestCase(unittest.TestCase):
    def test_setid(self):
        self.assertNotEqual(SetID(42), SetID(17))
        self.assertEqual(SetID(42), SetID('fiaaaaaaaaaaaaaaaaaaaaaaaa'))
        self.assertEqual(repr(SetID(42)), "SetID('fiaaaaaaaaaaaaaaaaaaaaaaaa')")
        self.assertEqual(str(SetID(42)), 'fiaaaaaaaaaaaaaaaaaaaaaaaa')
        setid = SetID(42)
        self.assertEqual(setid.lohi, (setid.lo, setid.hi))
        self.assertEqual(setid.lohi, (42, 0))
        self.assertEqual(int(setid), 42)
        self.assertEqual(SetID(42, 0), SetID(42))
        self.assertEqual(SetID(42, 1), SetID((1 << 64) + 42))

    def test_encode_decode_setid(self):
        setid = 2**128 - 1
        encoded = encode_setid(setid)
        decoded = decode_setid(encoded.lower())
        self.assertEqual(encoded, '77777777777777777777777774')
        self.assertEqual(decoded, setid)
