# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from collections import namedtuple
from numbers import Integral

from marv_api.iomsgs import CreateStream, GetRequested, MakeFile, Pull, PullAll, Push, SetHeader

from .mixins import Keyed, Request, Task

Fork = namedtuple('Fork', 'name inputs group')
GetStream = namedtuple('GetStream', 'setid node name')

# TODO: Rename
Request.register(Pull)
Request.register(PullAll)
Request.register(Push)
Request.register(SetHeader)

Request.register(CreateStream)
Request.register(Fork)
Request.register(GetRequested)
Request.register(GetStream)
Request.register(MakeFile)


class Signal(Task):  # pylint: disable=too-few-public-methods
    def __repr__(self):
        return type(self).__name__.upper()


class Next(Signal):  # pylint: disable=too-few-public-methods
    """Instruct to send next pending task."""

    __slots__ = ()


class Paused(Signal):  # pylint: disable=too-few-public-methods
    """Indicate a generator has paused."""

    __slots__ = ()


class Resume(Signal):  # pylint: disable=too-few-public-methods
    """Instruct a generator to resume."""

    __slots__ = ()


class TheEnd(Signal):  # pylint: disable=too-few-public-methods
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
        return f'MsgRequest({self._handle}, {self._idx!r})'
