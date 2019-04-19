# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=blacklisted-name

import unittest

from ..node import InputNameCollision, Node
from ..testing import marv


class TestCase(unittest.TestCase):
    def test_node_duplicate_input(self):
        with self.assertRaises(InputNameCollision):
            @marv.node()
            @marv.input('a')
            @marv.input('a')
            def no_inputs():  # pylint: disable=unused-variable
                yield

    @unittest.skip  # Do we want this?
    def test_node_without_inputs(self):
        @marv.node()
        def no_inputs():
            return 1
        self.assertEqual(no_inputs(), 1)

    def test_double_declare_node(self):
        with self.assertRaises(TypeError):
            @marv.node()
            @marv.node()
            def foo():  # pylint: disable=unused-variable
                yield  # pragma: nocoverage

    def test_node_repr(self):
        @marv.node()
        def foo():
            yield
        foo()
        self.assertEqual(
            repr(foo),
            '<Node foo.fy4oo6zcym>',
        )

    def test_comparisons(self):
        @marv.node()
        def a():  # pylint: disable=invalid-name
            yield

        @marv.node()
        def b():  # pylint: disable=invalid-name
            yield

        self.assertIs(type(a), type(b))
        self.assertIs(type(a), Node)
        self.assertIs(a, a)
        self.assertIsNot(a, b)

        self.assertLess(a.key, b.key)
        self.assertLess(a, b)
        self.assertLessEqual(a, b)
        self.assertLessEqual(a, a)
        self.assertEqual(a, a)
        self.assertNotEqual(a, b)
        self.assertGreater(b, a)
        self.assertGreaterEqual(b, a)
        self.assertGreaterEqual(b, b)

        self.assertEqual(a, a.clone())
