# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import unittest

from ..setid import SetID


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
