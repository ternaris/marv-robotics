# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=import-outside-toplevel

from collections import deque
from itertools import count
from numbers import Integral

from capnp.lib.capnp import KjException

from marv_api.setid import SetID
from marv_api.utils import NOTSET, err
from marv_pycapnp import Wrapper

from .mixins import Keyed, LoggerMixin, Request, Task


class RequestedMessageTooOld(Exception):
    """Indicate a message requested from a stream is not in memory anymore."""


class Handle(Keyed):
    @property
    def key(self):
        return (self.setid, self.node, self.name)

    @property
    def key_abbrev(self):
        return '.'.join([self.setid.abbrev, self.node.abbrev, self.name])

    def __init__(self, setid, node, name, group=None, header=None):
        # pylint: disable=too-many-arguments
        from .node import Node
        assert isinstance(setid, SetID), setid
        assert isinstance(node, Node), node
        self.setid = setid
        self.node = node
        self.name = name
        self.header = header or {}
        self.group = group if group is not None else self.node.group
        self._counter = count(-1)  # -1 will be the stream's handle

    def msg(self, __msg=None, _schema=NOTSET, **kw):
        from .io import TheEnd
        assert (__msg is not None) ^ bool(kw), (__msg, kw)
        data = kw if __msg is None else __msg
        if self.group:
            assert isinstance(data, (Handle, TheEnd)), (self, data)
        elif not isinstance(data, (Wrapper, Handle, TheEnd)):
            if _schema is NOTSET:
                from marv_api.ioctrl import NODE_SCHEMA  # pylint: disable=import-outside-toplevel
                schema = NODE_SCHEMA.get()
            else:
                schema = _schema
            if schema is not None:
                try:
                    data = Wrapper.from_dict(schema, data)
                except KjException:
                    from pprint import pformat  # pylint: disable=import-outside-toplevel
                    _node = schema.schema.node
                    err(f'Schema violation for {_node.displayName} with data:\n'
                        f'{pformat(data)}\nschema: {_node.displayName}')
                    raise
        return Msg(next(self._counter), self, data)

    def finish(self):
        from .io import THEEND
        return self.msg(THEEND)

    def create_stream(self, name, group=False, **header):
        assert self.group
        from .io import CreateStream
        return CreateStream(self, name, group, header)

    def make_file(self, name):
        from .io import MakeFile
        return MakeFile(self, name)

    def __getattr__(self, name):
        try:
            return self.header[name]
        except KeyError:
            raise AttributeError(name)

    def __repr__(self):
        return f'<{type(self).__name__} {self.key_abbrev}>'


class Msg(Keyed):
    @property
    def key(self):
        return (self._idx, self._handle)

    @property
    def idx(self):
        return self._idx

    @property
    def handle(self):
        return self._handle

    @property
    def data(self):
        return self._data

    def __init__(self, idx=None, handle=None, data=None):
        assert idx is None or isinstance(idx, Integral), idx
        assert isinstance(handle, Handle), handle
        self._idx = idx
        self._handle = handle
        self._data = data

    def __iter__(self):
        return iter([self._idx, self._handle, self._data])

    def __repr__(self):
        from .io import THEEND
        flags = ' HANDLE' if isinstance(self.data, Handle) else \
                ' THEEND' if self.data is THEEND else ''
        return f'Msg({self._idx}, {self.handle!r}{flags})'


Task.register(Msg)  # TODO: maybe not
Request.register(Msg)


class Stream(Keyed, LoggerMixin):
    CACHESIZE = 50
    cache = None
    ended = None
    handle = None

    @property
    def key(self):
        return self.handle.key

    @property
    def key_abbrev(self):
        return self.handle.key_abbrev

    @property
    def setid(self):
        return self.handle.setid

    @property
    def node(self):
        return self.handle.node

    @property
    def name(self):
        return self.handle.name

    @property
    def group(self):
        return self.handle.group

    def info(self):
        return [repr(msg) for msg in self.cache]  # pylint: disable=not-an-iterable

    def __repr__(self):
        return f'<{type(self).__name__} {self.key_abbrev}>'


Task.register(Stream)


class VolatileStream(Stream):
    def __init__(self, handle, parent=None):
        self.handle = handle
        self.parent = parent
        self.cache = deque((), self.CACHESIZE)

    def add_msg(self, msg):
        from .io import THEEND
        assert msg.handle == self.handle
        assert msg.idx is not None
        if self.group:
            assert isinstance(msg.data, Handle) or msg.data is THEEND, (self, msg)
        else:
            assert not isinstance(msg.data, Handle) or msg.idx == -1, (self, msg)

        expected_idx = self.cache[0].idx + 1 if self.cache else -1
        assert msg.idx == expected_idx, (msg.idx, expected_idx)
        self.cache.appendleft(msg)

        if msg.data is THEEND:
            self.ended = True

        self.logdebug('added %r', msg)

    def get_msg(self, req):
        assert req.handle == self.handle

        offset = self.cache[0].idx - req.idx if self.cache else -1
        if offset < 0:
            return None
        try:
            msg = self.cache[offset]
        except IndexError:
            raise RequestedMessageTooOld(req, offset)
        assert msg.data is not None
        self.logdebug('return %r', msg)
        return msg

    def create_stream(self, name, group, header=None):
        # TODO: check name collision?
        handle = Handle(self.setid, self.node, name, group=group, header=header)
        return type(self)(handle, parent=self)
