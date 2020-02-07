# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=blacklisted-name,invalid-name

import unittest

from ..node import Node
from ..testing import marv


@marv.node()
@marv.input('a', default=1)
def a_orig(a):  # pylint: disable=unused-argument
    yield


@marv.node()
@marv.input('a', default=1)
def b_orig(a):  # pylint: disable=unused-argument
    yield


class TestCase(unittest.TestCase):
    def test_node_repr(self):
        @marv.node()
        def foo():
            yield
        foo()
        self.assertEqual(
            repr(Node.from_dag_node(foo)),
            '<Node foo.fy4oo6zcym>',
        )

    def test_comparisons(self):
        a = Node.from_dag_node(a_orig)
        b = Node.from_dag_node(b_orig)
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

        self.assertEqual(a, Node.from_dag_node(a_orig.clone()))
        self.assertNotEqual(a, Node.from_dag_node(a_orig.clone(a=2)))
