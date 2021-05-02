# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import asyncio
import hashlib
from base64 import b32encode
from collections import OrderedDict, namedtuple
from contextlib import suppress
from itertools import count, product
from logging import getLogger

from marv_api import dag
from marv_api.ioctrl import NODE_SCHEMA, Abort
from marv_api.iomsgs import GetLogger, GetResourcePath
from marv_api.utils import find_obj

from . import io
from .mixins import Keyed

NODE_CACHE = {}


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
        spec_keys = repr(tuple(x.key for x in sorted(specs.values()))).encode()
        return b32encode(hashlib.sha256(spec_keys).digest()).decode().lower()[:-4]

    @classmethod
    def from_dag_node(cls, func):
        if hasattr(func, '__marv_node__'):
            dnode = func.__marv_node__
        else:
            dnode = func
            func = None

        node = NODE_CACHE.get(dnode)
        if node is not None:
            return node

        if func is None:
            func = find_obj(dnode.function)
        namespace, name = dnode.function.rsplit('.', 1)
        schema = find_obj(dnode.message_schema) if dnode.message_schema is not None else None
        inputs = dnode.inputs
        specs = OrderedDict((
            (name, InputSpec(name=name,
                             value=(value if not isinstance(value, dag.Stream) else
                                    StreamSpec(node=Node.from_dag_node(value.node),
                                               name=value.name)),
                             foreach=name == dnode.foreach))
            for name, value in ((name, getattr(inputs, name)) for name in inputs.__fields__.keys())
        ))
        node = cls(func,
                   schema=schema,
                   version=dnode.version,
                   name=name,
                   namespace=namespace,
                   specs=specs,
                   group=dnode.group,
                   dag_node=dnode)
        NODE_CACHE[dnode] = node
        return node

    def __init__(self, func, schema=None, version=None,
                 name=None, namespace=None, specs=None, group=None, dag_node=None):
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

        if self.fullname == 'marv_nodes:dataset':
            self.load = func.load

        assert dag_node is not None
        self.dag_node = dag_node

    def __call__(self, **inputs):
        return self.func(**inputs)

    async def invoke(self, key_abbrev, inputs=None, site=None):  # noqa: C901
        # pylint: disable=too-many-locals,too-many-branches,too-many-statements
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
            log = getLogger(f'marv.node.{key_abbrev}')
            cross = product(*[[(k, x) for x in v] for k, v in foreach_plain])
            if foreach_stream:
                assert len(foreach_stream) == 1, self  # FOR NOW
                cross = list(cross)
                name, stream = foreach_stream[0]
                idx = count()
                while True:
                    value = yield io.Pull(stream, False)
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
            qout, qin = asyncio.Queue(1), asyncio.Queue(1)
            task = asyncio.create_task(self.execnode(key_abbrev, inputs, qin=qout, qout=qin,
                                                     site=site),
                                       name=key_abbrev)
            while True:
                request = await qin.get()
                if request is None:
                    await task
                    break
                try:
                    response = yield request
                except GeneratorExit:
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        await task
                    break

                qout.put_nowait(response)

    async def execnode(self, key_abbrev, inputs, qin, qout, site=None):
        NODE_SCHEMA.set(self.schema)
        gen = self.func(**inputs)
        assert hasattr(gen, 'send')
        response = None
        log = getLogger(f'marv.node.{key_abbrev}')
        while True:
            try:
                request = gen.send(response)
            # TODO: Abort exception needs to invalidate previous node output
            except (Abort, StopIteration) as exc:
                msg = str(exc)
                if msg:
                    log.warning(msg)
                qout.put_nowait(None)
                return
            except BaseException:  # pylint: disable=broad-except
                qout.put_nowait(None)
                raise

            if isinstance(request, GetLogger):
                response = log
                continue

            if isinstance(request, GetResourcePath):
                response = site.config.marv.resourcedir / request.name
                continue

            qout.put_nowait(request)
            response = await qin.get()

    def __str__(self):
        return self.key

    def __repr__(self):
        return f'<Node {self.abbrev}>'
