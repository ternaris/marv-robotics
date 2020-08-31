# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=blacklisted-name,unused-variable,unused-argument

import capnp  # pylint: disable=unused-import
import pytest

import marv_api as marv
from marv_api.dag import Stream
from marv_api.decorators import NOTSET, getdag

from .types_capnp import Test  # pylint: disable=import-error


def test():
    @marv.node()
    def source():
        yield  # pragma: nocoverage

    @marv.node(Test, group='ondemand', version=1)
    @marv.input('foo', default=1)
    @marv.input('bar', type=int)
    @marv.input('baz', default=source)
    @marv.input('qux', foreach=marv.select(source, 'stream'))
    def consumer(foo, bar, baz, qux):
        yield  # pragma: nocoverage

    node = consumer.__marv_node__
    assert node.function == 'marv_api.tests.test_decorators.test.<locals>.consumer'
    assert node.inputs.__fields__.keys() == {'foo', 'bar', 'baz', 'qux'}
    assert node.inputs.__annotations__ == {'bar': int}
    assert node.inputs.foo == 1
    assert node.inputs.bar == NOTSET
    assert node.inputs.baz == Stream(node=getdag(source))
    assert node.inputs.qux == Stream(node=getdag(source), name='stream')
    assert node.message_schema == 'marv_api.tests.types_capnp:Test'
    assert node.group == 'ondemand'
    assert node.version == 1
    assert node.foreach == 'qux'


def test_clone():
    @marv.node()
    def source1():
        yield  # pragma: nocoverage

    @marv.node()
    def source2():
        yield  # pragma: nocoverage

    @marv.node()
    @marv.input('foo', default=1)
    @marv.input('stream', default=source1)
    def consumer(foo, stream):
        yield  # pragma: nocoverage

    clone = consumer.clone(foo=10, stream=source2)
    assert clone.inputs.foo == 10
    assert clone.inputs.stream == Stream(node=getdag(source2))

    clone = consumer.clone(stream=marv.select(source2, 'foo'))
    assert clone.inputs.stream == Stream(node=getdag(source2), name='foo')


def test_duplicate_input_fails():
    with pytest.raises(marv.InputNameCollision):
        @marv.input('a', type=int)
        @marv.input('a', type=int)
        def collision():
            pass  # pragma: nocoverage


def test_multi_foreach_fails():
    # NOTE: foreach is an internal deprecated feature
    with pytest.raises(AssertionError):
        @marv.input('foo', foreach='invalid')
        @marv.input('bar', foreach='invalid')
        def collision():
            pass  # pragma: nocoverage


def test_either_default_or_foreach():
    with pytest.raises(AssertionError):
        @marv.input('foo', 1, foreach='invalid')
        def foo():
            pass  # pragma: nocoverage


def test_non_generator_fails():
    with pytest.raises(TypeError):
        @marv.node()
        def foo():
            pass  # pragma: nocoverage


def test_no_inputs():
    @marv.node()
    def source():
        yield 1

    assert source.__marv_node__.inputs.__fields__ == {}
    assert list(source()) == [1]


def test_func_works_normal():
    @marv.node()
    @marv.input('bar', default=1)
    def foo(bar):
        yield bar

    with pytest.raises(TypeError) as einfo:
        assert foo()  # pylint: disable=no-value-for-parameter
    assert einfo.match('missing 1 required positional argument')
    assert list(foo(10)) == [10]


def test_convert_twice():
    with pytest.raises(TypeError) as einfo:
        @marv.node()
        @marv.node()
        def foo():
            yield  # pragma: nocoverage
    assert einfo.match('twice')


def test_type_or_default_for_input():
    with pytest.raises(TypeError) as einfo:
        @marv.input('abc')
        def foo():
            yield  # pragma: nocoverage
    assert einfo.match("'type' is needed")


def test_no_type_for_streams():
    @marv.node()
    def source():
        yield  # pragma: nocoverage

    with pytest.raises(TypeError) as einfo:
        @marv.input('abc', default=source, type=int)
        def foo():
            yield  # pragma: nocoverage
    assert einfo.match("'type' is not")


def test_missing_input_declaration():
    with pytest.raises(TypeError) as einfo:
        @marv.node()
        def foo(abc):
            yield  # pragma: nocoverage
    assert einfo.match('Missing input')


def test_unsupported_func_sig():
    with pytest.raises(TypeError) as einfo:
        @marv.node()
        def foo(*args):
            yield  # pragma: nocoverage
    assert einfo.match('Only positional')

    with pytest.raises(TypeError) as einfo:
        @marv.node()
        @marv.input('abc', 1)
        def bar(abc=1):
            yield  # pragma: nocoverage
    assert einfo.match('Only positional')

    with pytest.raises(TypeError) as einfo:
        @marv.node()
        @marv.input('abc', 1)
        def baz(abc: int):
            yield  # pragma: nocoverage
    assert einfo.match('Only positional')


def test_not_called():
    with pytest.raises(TypeError) as einfo:
        @marv.node
        def foo(*args):
            yield  # pragma: nocoverage
    assert einfo.match('must be called')
