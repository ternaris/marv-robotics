# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

from collections import namedtuple
from numbers import Integral

from .mixins import Keyed, Task, Request
from .stream import Handle


class Abort(Exception):
    pass


def create_stream(name, **header):
    """Create a stream for publishing messages.

    All keyword arguments will be used to form the header.
    """
    assert isinstance(name, basestring), name
    return CreateStream(parent=None, name=name, group=False, header=header)


def create_group(name, **header):
    assert isinstance(name, basestring), name
    return CreateStream(parent=None, name=name, group=True, header=header)


def fork(name, inputs, group):
    assert isinstance(name, basestring), name
    assert inputs
    return Fork(name, inputs, group)


def get_logger():
    return GetLogger()


def get_requested():
    return GetRequested()


def get_stream(node, name='default', setid=None):
    return GetStream(setid, node, name)


def make_file(name):
    assert isinstance(name, basestring)
    return MakeFile(None, name)


def pull(handle, enumerate=False):
    """Pulls next message for handle.

    Args:
        handle: A :class:`.stream.Handle` or GroupHandle.
        enumerate (bool): boolean to indicate whether a tuple ``(idx, msg)``
            should be returned, not unlike Python's enumerate().

    Returns:
        A :class:`Pull` task to be yielded. Marv will send the
        corresponding message as soon as it is available. For groups
        this message will be a handle to a member of the
        group. Members of groups are either streams or groups.

    Examples:
        Pulling (enumerated) message from stream::

            msg = yield marv.pull(stream)
            idx, msg = yield marv.pull(stream, enumerate=True)

        Pulling stream from group and message from stream::

            stream = yield marv.pull(group)  # a group of streams
            msg = yield marv.pull(stream)

    """
    assert isinstance(handle, Handle), handle
    return Pull(handle, enumerate)


def pull_all(*handles):
    """Pulls next message of all handles."""
    return PullAll(handles)


def pull_any(handles):
    raise NotImplementedError


def push(msg):
    return Push(msg)


def set_header(**header):
    """Set the header of a stream or group."""

    # If a node is configured to have a header, the header needs to be
    # set before yielding any messages or creating group members. Once a
    # header is set, a handle is created and dependent nodes can be
    # instantiated. For streams without headers this happens right away.

    #     @marv.node(header=True)
    #     def node():
    #         yield marv.set_header(title='Title')

    # """
    return SetHeader(header)


CreateStream = namedtuple('CreateStream', 'parent name group header')
Fork = namedtuple('Fork', 'name inputs group')
GetLogger = namedtuple('GetLogger', '')
GetRequested = namedtuple('GetRequested', '')
GetStream = namedtuple('GetStream', 'setid node name')
MakeFile = namedtuple('MakeFile', 'handle name')

Pull = namedtuple('Pull', 'handle enumerate')
PullAll = namedtuple('PullAll', 'handles')
PullAny = namedtuple('PullAny', 'handles')
PullSome = namedtuple('PullSome', 'handles')
Push = namedtuple('Push', 'output')
SetHeader = namedtuple('SetHeader', 'header')

# TODO: Rename
Request.register(Pull)
Request.register(PullAll)
Request.register(PullAny)
Request.register(PullSome)
Request.register(Push)
Request.register(SetHeader)

Request.register(CreateStream)
Request.register(Fork)
Request.register(GetLogger)
Request.register(GetRequested)
Request.register(GetStream)
Request.register(MakeFile)


class Signal(Task):
    def __repr__(self):
        return type(self).__name__.upper()

class Next(Signal):
    """Instruct to send next pending task."""
    __slots__ = ()

class Paused(Signal):
    """Indicate a generator has paused."""
    __slots__ = ()

class Resume(Signal):
    """Instruct a generator to resume."""
    __slots__ = ()

class TheEnd(Signal):
    """Indicate the end of a stream, resulting in None being sent into consumers."""
    __slots__ = ()

NEXT = Next()
PAUSED = Paused()
RESUME = Resume()
THEEND = TheEnd()


class MsgRequest(Task, Keyed):
    __slots__ = ('_handle', '_idx', '__weakref__')

    @property
    def key(self):
        return (self._handle, self._idx)

    @property
    def handle(self):
        return self._handle

    @property
    def idx(self):
        return self._idx

    def __init__(self, handle, idx, requestor):
        assert isinstance(idx, Integral), idx
        self._handle = handle
        self._idx = idx
        self._requestor = requestor

    def __iter__(self):
        return iter(self.key)

    def __repr__(self):
        return 'MsgRequest({}, {!r})'.format(self._handle, self._idx)
