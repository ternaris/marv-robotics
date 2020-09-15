# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=blacklisted-name,unused-variable,unused-argument,too-few-public-methods

import marv_api as marv
from marv_api.dag import Model
from marv_api.decorators import getdag


@marv.node()
def source1():
    yield  # pragma: nocoverage


@marv.node()
def source2():
    yield  # pragma: nocoverage


@marv.node()
@marv.input('foo', type=int)
@marv.input('stream', default=source1)
def consumer(foo, stream):
    yield  # pragma: nocoverage


class Foo(Model):
    xyz: int


class Bar(Model):
    xyz: int


def test_hashable():
    assert hash(Foo(xyz=1)) != hash(Bar(xyz=1))
    assert hash(getdag(source1)) != hash(getdag(source2))
    assert hash(getdag(consumer)) != hash(consumer.clone(foo=1))
    assert hash(consumer.clone(foo=1)) == hash(consumer.clone(foo=1))
    assert hash(getdag(consumer)) != hash(consumer.clone(stream=source2))
    assert hash(consumer.clone(stream=source2)) == hash(consumer.clone(stream=source2))
    assert hash(consumer.clone(stream=marv.select(source2, name='foo'))) != \
        hash(consumer.clone(stream=marv.select(source2, name='bar')))
    assert hash(consumer.clone(stream=marv.select(source2, name='foo'))) == \
        hash(consumer.clone(stream=marv.select(source2, name='foo')))
