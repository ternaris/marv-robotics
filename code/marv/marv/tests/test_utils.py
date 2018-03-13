# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import unittest

from ..utils import decode_setid, encode_setid


class TestCase(unittest.TestCase):
    def test_encode_decode_setid(self):
        setid = 2**128 - 1
        encoded = encode_setid(setid)
        decoded = decode_setid(encoded.lower())
        self.assertEqual(encoded, '77777777777777777777777774')
        self.assertEqual(decoded, setid)
