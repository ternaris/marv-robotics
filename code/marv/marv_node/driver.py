# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

from collections import OrderedDict, defaultdict
from itertools import count
from logging import getLogger

from capnp.lib.capnp import KjException

from marv_pycapnp import Wrapper
from .io import Abort
from .io import NEXT, PAUSED, RESUME, THEEND, TheEnd
from .io import SetHeader, CreateStream, Fork, GetRequested, GetStream
from .io import GetLogger, Task, MsgRequest, MakeFile
from .io import Pull, PullAll, Push
from .mixins import GenWrapperMixin, LoggerMixin
from .node import Keyed
from .stream import Handle, Msg


class MakeFileNotSupported(Exception):
    """Only persistent streams can make files."""


class Driver(Keyed, GenWrapperMixin, LoggerMixin):
    """Drives a generator."""
    key = None
    started = False
    stopped = False
    stream_creation = True  # False after first output Msg() TODO

    @property
    def key(self):
        return self.stream.key

    @property
    def key_abbrev(self):
        return self.stream.key_abbrev

    @property
    def setid(self):
        return self.stream.setid

    @property
    def node(self):
        return self.stream.node

    @property
    def name(self):
        return self.stream.name

    def __init__(self, stream, inputs=None):
        self.stream = stream
        self.streams = OrderedDict([(stream.handle, stream)])
        self.inputs = inputs
        self._requested_streams = []
        self._gen = self._run()

    def start(self):
        req = self.next()
        assert req is None
        return NEXT

    def __repr__(self):
        return '<{} {}>'.format(type(self).__name__, self.key_abbrev)

    def _run(self):
        self.started = True

        gen = self.node.invoke(self.inputs)
        assert hasattr(gen, 'send'), gen

        yield  # Wait for start signal before returning anything notable
        yield self.stream

        request_counter = count()
        msg_request_counter = defaultdict(count)
        next_msg_index_counter = defaultdict(int)
        send = None
        finished = False
        while not finished:
            try:
                request = gen.send(send)
                self.logdebug('got from node %s', type(request))
                request_idx = request_counter.next()
            except StopIteration:
                finished = True
            except Abort:
                finished = True

            if finished:
                for stream in self.streams.values():
                    if len(stream.cache) == 0:
                        yield stream.handle.msg(stream.handle)
                    if len(stream.cache) == 1:
                        self.logdebug('finishing empty stream')
                    if not stream.ended:
                        yield stream.handle.msg(THEEND)
                break

            output = None

            # preprocess
            # TODO:
            # - yield out.msg() valid? or enfore
            # - yield marv.push(out.msg(foo)) or
            # - yield marv.push(foo, out)
            if isinstance(request, Push):
                output = request.output
            elif isinstance(request, (Msg, Wrapper)):
                output = request

            # process
            if output:
                if len(self.stream.cache) == 0:
                    yield self.stream.handle.msg(self.stream.handle)

                # With first output, stream creation is done
                if self.stream_creation:
                    self.stream_creation = False

                msg = output
                if not isinstance(msg, Msg):
                    msg = self.stream.handle.msg(msg)
                else:
                    assert msg.handle.node is self.node
                    assert msg.handle.setid == self.setid
                schema = self.node.schema
                # TODO: handles should not be published by all?
                # this got introduced for merging streams
                if isinstance(msg._data, Handle):
                    # TODO: check that stream we are publishing to is a Group
                    assert self.node.group, self.node
                if schema is not None and \
                   not isinstance(msg._data, (Wrapper, Handle, TheEnd)):
                    try:
                        msg._data = Wrapper.from_dict(schema, msg._data)
                    except KjException as e:
                        from pprint import pformat
                        self.logerror(
                            'Schema violation for %s with data:\n%s\nschema: %s',
                            schema.schema.node.displayName,
                            pformat(msg._data),
                            schema.schema.node.displayName)
                        raise e
                signal = yield msg
                assert signal in (NEXT, RESUME), signal
                continue

            elif isinstance(request, Pull):
                handle = request.handle
                # if request.skip is never used the two indices remain the same
                msg_req_idx = msg_request_counter[handle].next()
                next_msg_idx = next_msg_index_counter[handle]  # + request.skip
                next_msg_index_counter[handle] = next_msg_idx + 1
                msg = yield MsgRequest(handle, next_msg_idx, self)
                assert isinstance(msg, Msg), msg
                assert msg.idx == next_msg_idx
                # TODO: switch to DONE
                send = None if msg.data is THEEND else msg.data
                if request.enumerate:
                    send = (msg_req_idx, send)
                continue

            elif isinstance(request, PullAll):
                send = []
                for handle in request.handles:
                    msg_req_idx = msg_request_counter[handle].next()
                    next_msg_idx = next_msg_index_counter[handle]
                    next_msg_index_counter[handle] = next_msg_idx + 1
                    msg = yield MsgRequest(handle, next_msg_idx, self)
                    assert isinstance(msg, Msg), msg
                    assert msg.idx == next_msg_idx
                    # TODO: switch to DONE
                    send.append(None if msg.data is THEEND else msg.data)
                continue

            elif isinstance(request, SetHeader):
                # TODO: should this be explicitly allowed/required?
                # Handles for non-header streams would be created right away
                assert len(self.stream.cache) == 0
                self.stream.handle.header = request.header.copy()
                yield self.stream.handle.msg(self.stream.handle)
                continue

            elif isinstance(request, MakeFile):
                if len(self.stream.cache) == 0:
                    yield self.stream.handle.msg(self.stream.handle)
                stream = self.streams[request.handle or self.stream.handle]
                try:
                    make_file = stream.make_file
                except AttributeError:
                    raise MakeFileNotSupported(stream)
                send = make_file(request.name)
                continue

            elif isinstance(request, Fork):
                parent_handle = self.stream.handle
                parent = self.streams[parent_handle]
                stream = parent.create_stream(name=request.name,
                                              group=request.group)
                fork = type(self)(stream, inputs=request.inputs)
                if len(self.stream.cache) == 0:
                    yield self.stream.handle.msg(self.stream.handle)
                yield fork
                send = None   # TODO: What should we send back?
                continue

            elif isinstance(request, GetStream):
                handle = Handle(request.setid or self.setid,
                                request.node, request.name)
                msg = yield MsgRequest(handle, -1, self)
                send = msg.data
                assert send == handle, (send, handle)
                continue  # TODO: why is this not covered?

            elif isinstance(request, CreateStream):
                kw = request._asdict()
                parent_handle = kw.pop('parent', None) or self.stream.handle
                parent = self.streams[parent_handle]
                stream = parent.create_stream(**kw)
                assert stream.name != 'default'
                assert stream.handle not in self.streams, stream
                self.streams[stream.handle] = stream
                if len(parent.cache) == 0:
                    yield parent.handle.msg(parent.handle)
                if len(self.stream.cache) == 0:
                    yield self.stream.handle.msg(self.stream.handle)
                yield stream
                yield stream.handle.msg(stream.handle)
                send = stream.handle
                continue

            elif isinstance(request, GetRequested):
                assert self.stream.group, (self, request)
                signal = yield PAUSED  # increase chances for completeness
                assert signal is RESUME
                send = list(self._requested_streams)
                self.stream_creation = False
                continue

            elif isinstance(request, GetLogger):
                send = getLogger('marv.node.{}'.format(self.key_abbrev))
                continue

            else:
                raise RuntimeError('Unknown request number {}: {!r} from {!r}'
                                   .format(request_idx + 1, request, self.node))
        self.stopped = True

    def add_stream_request(self, *handles):
        assert self.stream_creation
        assert self.node.group == 'ondemand'
        for handle in sorted(handles):
            if handle not in self._requested_streams:
                self._requested_streams.append(handle)
                self.logdebug('REQFILED %s', handle.key_abbrev)

    def destroy(self):
        for stream in self.streams.values():
            stream.destroy()

Task.register(Driver)
