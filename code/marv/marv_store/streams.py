# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import os
from collections import OrderedDict, deque
from pathlib import Path

from marv_node.io import THEEND
from marv_node.stream import Handle, Msg, RequestedMessageTooOld, Stream
from marv_nodes.types_capnp import File  # pylint: disable=no-name-in-module
from marv_pycapnp import Wrapper


class ReadStream(Stream):
    streamfile = None

    def __init__(self, prehandle, streamdir, setdir, msgs=None, info=None):
        # pylint: disable=too-many-arguments
        header = info['header'] if info else {}
        handle = Handle(*prehandle.key, group=prehandle.group, header=header)
        self.handle = handle
        self.cache = deque([Msg(idx=-1, handle=handle, data=handle)], self.CACHESIZE)
        if handle.group:
            self.stream = iter([
                Handle(handle.setid, handle.node, x['name'],
                       group=bool(x['streams']),
                       header=x['header'])
                for x in info['streams'].values()
            ])
        elif msgs:
            # pylint: disable=protected-access
            self.stream = (Wrapper(x._reader, streamdir, setdir) for x in msgs)
        else:
            assert not info['streams']
            path = os.path.join(streamdir, f'{handle.name}-stream')
            streamfile = open(path, 'rb')
            self.streamfile = streamfile
            self.stream = (Wrapper(x, streamdir, setdir) for x in
                           handle.node.schema.read_multiple_packed(streamfile))

    def get_msg(self, req):
        self.logdebug('got %r', req)
        assert req.handle == self.handle

        latest_idx = self.cache[0].idx
        offset = latest_idx - req.idx if self.cache else -1
        if offset < 0:
            assert offset == -1  # for now
            try:
                data = next(self.stream)
            except StopIteration:
                data = THEEND
                if self.streamfile:
                    self.streamfile.close()
                self.ended = True
            msg = Msg(latest_idx + 1, req.handle, data)
            self.cache.appendleft(msg)
        else:
            try:
                msg = self.cache[offset]
            except IndexError:
                raise RequestedMessageTooOld(req, offset)
        assert msg.data is not None
        self.logdebug('return %r', msg)
        return msg


class PersistentStream(Stream):
    # pylint: disable=too-many-instance-attributes

    ended = False

    def __init__(self, handle, streamdir, setdir, commit, parent=None):
        # pylint: disable=too-many-arguments
        self.parent = parent
        self.handle = handle
        self.streamdir = streamdir
        self.setdir = setdir
        self.cache = deque((), self.CACHESIZE)
        self.streams = OrderedDict() if self.group else None
        # open right away: empty stream -> empty file
        path = os.path.join(streamdir, f'{handle.name}-stream')
        self.streamfile = None if self.group else open(path, 'wb')
        self.done = set()
        self._commit = commit

    def add_msg(self, msg):
        assert not self.ended
        assert msg.handle == self.handle
        assert msg.idx is not None
        if self.group:
            assert isinstance(msg.data, Handle) or msg.data is THEEND, (self, msg)
        else:
            assert not isinstance(msg.data, Handle) or msg.idx == -1, (self, msg)

        expected_idx = self.cache[0].idx + 1 if self.cache else -1
        assert msg.idx == expected_idx, (msg.idx, expected_idx)

        self.logdebug('adding %r', msg)
        # pylint: disable=protected-access
        if msg.data is THEEND:
            self.ended = True
            self.logdebug('ended')
            if not self.group or self.done == self.streams.keys():
                self._commit(self)
        elif isinstance(msg.data, Wrapper) \
                and msg.data._reader.schema.node.id == File.schema.node.id:
            assert msg.data._streamdir == Path(self.streamdir)
            stat = os.stat(msg.data.path)
            mtime = int(stat.st_mtime * 1e9)
            msg.data._reader = File.new_message(path=msg.data._reader.path,
                                                mtime=mtime, size=stat.st_size)\
                                   .as_reader()
        self.cache.appendleft(msg)
        if not self.group and msg.idx >= 0:
            # TODO: Maybe we want to have a builder and change to
            # reader before putting in cache?
            try:
                write_packed = msg.data._reader.as_builder().write_packed
            except AttributeError:
                assert msg.data is THEEND
                self.streamfile.close()
                return
            write_packed(self.streamfile)

    def get_msg(self, req):
        assert req.handle == self.handle

        offset = self.cache[0].idx - req.idx if self.cache else -1
        if offset < 0:
            assert not self.ended
            return None

        try:
            msg = self.cache[offset]
        except IndexError:
            raise RequestedMessageTooOld(req, offset)
        assert msg.data is not None
        self.logdebug('return %r', msg)
        return msg

    def create_stream(self, name, group, header=None):
        assert self.group
        assert not self.ended
        handle = Handle(self.handle.setid, self.handle.node, name, group=group, header=header)
        stream = type(self)(handle, self.streamdir, self.setdir,
                            self.commit_substream, parent=self)
        self.streams[handle.name] = stream
        return stream

    def commit_substream(self, substream):
        self.done.add(substream.handle.name)
        if self.ended and self.done == self.streams.keys():
            self._commit(self)

    def make_file(self, name):
        assert not self.ended
        assert not self.group, (self, name)
        path = os.path.join(self.streamdir, name)
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666)
        os.close(fd)  # shall we pass on the open handle?
        # TODO: consider storing path relative to setdir instead of name
        file = File.new_message(path=path).as_reader()
        wrapper = Wrapper(file, self.streamdir, self.setdir)
        self.logdebug('made file %r', wrapper)
        return wrapper
