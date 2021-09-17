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

    def test_node_repr(self):  # pylint: disable=no-self-use

        @marv.node()
        def foo():
            yield

        foo()
        assert repr(Node.from_dag_node(foo)) == '<Node foo.fy4oo6zcym>'

    def test_comparisons(self):  # pylint: disable=no-self-use
        # pylint: disable=comparison-with-itself
        a = Node.from_dag_node(a_orig)
        b = Node.from_dag_node(b_orig)
        assert type(a) is type(b)
        assert isinstance(a, Node)
        assert a is a
        assert a is not b

        assert a.key < b.key
        assert a < b
        assert a <= b
        assert a <= a
        assert a == a
        assert a != b
        assert b > a
        assert b >= a
        assert b >= b

        assert a == Node.from_dag_node(a_orig.clone())
        assert a != Node.from_dag_node(a_orig.clone(a=2))
