# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import unittest


class TestCase(unittest.TestCase):
    def test_(self):
        from . import pythonic_capnp

        # class Pythonic(Base):
        #     """foo"""
        #     schema = pythonic_capnp.Pythonic

        import capnp
        p = pythonic_capnp.Pythonic.new_message()
        r = p.as_reader()
