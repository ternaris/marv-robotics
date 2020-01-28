# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import hashlib
from base64 import b32encode
from collections import namedtuple
from itertools import count, product

from . import io
from .io import get_logger, pull
from .mixins import Keyed


class InputSpec(Keyed, namedtuple('InputSpec', ('name', 'value', 'foreach'))):
    @property
    def key(self):
        value = self.value.key if hasattr(self.value, 'key') else self.value
        return (self.name, value, self.foreach)

    def clone(self, value):
        cls = type(self)
        value = StreamSpec(value) if isinstance(value, Node) else value
        return cls(self.name, value, self.foreach)

    def __repr__(self):
        foreach = 'foreach ' if self.foreach else ''
        return f'<{type(self)} {foreach}{self.name}={self.value!r}>'


class StreamSpec:  # pylint: disable=too-few-public-methods
    def __init__(self, node, name=None):  # pylint: disable=redefined-outer-name
        assert isinstance(node, Node)
        self.node = node
        self.name = name
        self.key = (node.key,) if name is None else (node.key, name)
        self.args = (node,) if name is None else (node, name)


class Node(Keyed):  # pylint: disable=too-many-instance-attributes
    _key = None
    group = None

    @property
    def key(self):
        key = self._key
        if key:
            return key
        return '-'.join([self.specs_hash, self.fullname])

    @property
    def abbrev(self):
        return '.'.join([self.name, self.specs_hash[:10]])

    @staticmethod
    def genhash(specs):
        spec_keys = repr(tuple(x.key for x in sorted(specs.values()))).encode('utf-8')
        return b32encode(hashlib.sha256(spec_keys).digest()).decode('utf-8').lower()[:-4]

    def __init__(self, func, schema=None, version=None,
                 name=None, namespace=None, specs=None, group=None):
        # pylint: disable=too-many-arguments
        # TODO: assert no default values on func, or consider default
        # values (instead of) marv.input() declarations
        # Definitely not for node inputs as they are not passed directly!
        self.func = func
        self.version = version
        self.name = name = func.__name__ if name is None else name
        self.namespace = namespace = func.__module__ if namespace is None else namespace
        self.fullname = (name if not namespace else ':'.join([namespace, name]))
        self.specs_hash = self.genhash(specs or {})
        self.schema = schema
        self.specs = specs or {}
        assert group in (None, False, True, 'ondemand'), group
        self.group = (group if group is not None else
                      any(x.foreach for x in self.specs.values()))
        # TODO: StreamSpec, seriously?
        self.deps = {x.value.node for x in self.specs.values()
                     if isinstance(x.value, StreamSpec)}
        self.alldeps = self.deps.copy()
        self.alldeps.update(x for dep in self.deps
                            for x in dep.alldeps)

        self.consumers = set()
        for dep in self.deps:
            assert self not in dep.consumers, (dep, self)
            dep.consumers.add(self)

        self.dependent = set()
        for dep in self.alldeps:
            assert self not in dep.dependent, (dep, self)
            dep.dependent.add(self)

    def __call__(self, **inputs):
        return self.func(**inputs)

    async def invoke(self, inputs=None):  # noqa: C901
        # pylint: disable=too-many-locals,too-many-branches
        # We must not write any instance variables, a node is running
        # multiple times in parallel.

        common = []
        foreach_plain = []
        foreach_stream = []
        if inputs is None:
            for spec in self.specs.values():
                assert not isinstance(spec.value, Node), (self, spec.value)
                if isinstance(spec.value, StreamSpec):
                    value = yield io.GetStream(setid=None, node=spec.value.node,
                                               name=spec.value.name or 'default')
                    target = foreach_stream if spec.foreach else common
                else:
                    value = spec.value
                    target = foreach_plain if spec.foreach else common
                target.append((spec.name, value))

        if foreach_plain or foreach_stream:
            log = yield get_logger()
            cross = product(*[[(k, x) for x in v] for k, v in foreach_plain])
            if foreach_stream:
                assert len(foreach_stream) == 1, self  # FOR NOW
                cross = list(cross)
                name, stream = foreach_stream[0]
                idx = count()
                while True:
                    value = yield pull(stream)
                    if value is None:
                        log.noisy('finished forking')
                        break
                    for inputs in cross:  # pylint: disable=redefined-argument-from-local
                        inputs = dict(inputs)
                        inputs.update(common)
                        inputs[name] = value
                        # TODO: give fork a name
                        _idx = next(idx)
                        log.noisy('FORK %d with: %r', _idx, inputs)
                        yield io.Fork(f'{_idx}', inputs, False)
            else:
                # pylint: disable=redefined-argument-from-local
                for _idx, inputs in enumerate(cross):
                    # TODO: consider deepcopy
                    inputs = dict(inputs)
                    inputs.update(common)
                    log.noisy('FORK %d with: %r', _idx, inputs)
                    yield io.Fork(f'{_idx}', inputs, False)
                log.noisy('finished forking')
        else:
            if inputs is None:
                inputs = dict(common)
            gen = self.func(**inputs)
            assert hasattr(gen, 'send')
            response = None
            while True:
                try:
                    request = gen.send(response)
                except StopIteration:
                    return
                response = yield request

    def clone(self, **kw):
        specs = {spec.name: (spec if spec.name not in kw else
                             spec.clone(kw.pop(spec.name)))
                 for spec in self.specs.values()}
        assert not kw, (kw, self.specs)
        cls = type(self)
        clone = cls(func=self.func, schema=self.schema, specs=specs)
        return clone

    def __str__(self):
        return self.key

    def __repr__(self):
        return f'<Node {self.abbrev}>'
