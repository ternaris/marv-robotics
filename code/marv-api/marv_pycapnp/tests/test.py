# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=no-self-use

import unittest


class TestCase(unittest.TestCase):
    def test_(self):
        from . import pythonic_capnp  # pylint: disable=no-name-in-module,import-outside-toplevel

        # class Pythonic(Base):
        #     """foo"""
        #     schema = pythonic_capnp.Pythonic

        builder = pythonic_capnp.Pythonic.new_message()
        reader = builder.as_reader()
        assert reader
