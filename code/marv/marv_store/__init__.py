# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import json
import os
from collections import Mapping, defaultdict

from marv_node.mixins import LoggerMixin
from marv_pycapnp import Wrapper
from .streams import PersistentStream, ReadStream


class DirectoryAlreadyExists(Exception):
    """Temporary directory for next generation of stream already exists

    This might mean another node run is in progress or aborted without
    proper cleanup.
    """


class Store(Mapping, LoggerMixin):
    def __init__(self, path, nodes):
        self.path = path
        self.pending = {}
        self.nodes = nodes
        self.name_by_node = {v: k for k, v in nodes.items()}

    def has_setid(self, setid):
        return os.path.isdir(os.path.join(self.path, str(setid)))

    def __getitem__(self, handle):
        setdir = os.path.join(self.path, str(handle.setid))
        name = self.name_by_node.get(handle.node, handle.node.name)
        symlink = os.path.join(setdir, name)
        try:
            gendir = os.readlink(symlink)
        except OSError:
            raise KeyError(handle)
        streamdir = os.path.join(setdir, gendir)
        if not os.path.exists(streamdir):
            raise KeyError(handle)
        with open(os.path.join(streamdir, 'streams.json')) as f:
            streams = json.load(f)
        if handle.name != 'default':
            streams = streams['streams'][handle.name]
        return ReadStream(handle, streamdir, setdir, info=streams)

    def __iter__(self):
        raise NotImplementedError()

    def __len__(self):
        raise NotImplementedError()

    def add_dataset(self, dataset):
        setdir = os.path.join(self.path, str(dataset.setid))
        os.mkdir(setdir)

    def create_stream(self, handle):
        assert handle.name == 'default', handle
        setdir = os.path.join(self.path, str(handle.setid))
        assert os.path.exists(setdir), setdir
        name = self.name_by_node.get(handle.node, handle.node.name)
        symlink = os.path.join(setdir, name)
        try:
            curgen = int(os.readlink(symlink).rsplit('-')[-1])
        except OSError:
            curgen = 0
        next_name = '{}-{}'.format(name, curgen + 1)
        nextdir = os.path.join(setdir, next_name)
        newlink = os.path.join(setdir, '.{}'.format(name))
        tmpdir = os.path.join(setdir, '.' + next_name)
        try:
            os.mkdir(tmpdir)
        except OSError:
            self.logerror('directory exists %r', tmpdir)
            raise DirectoryAlreadyExists(tmpdir)
        self.logdebug('created directory %r', tmpdir)

        def commit(stream):
            assert not stream.group or stream.done == stream.streams.viewkeys()
            self.lognoisy('committing %r', nextdir)
            streams = self._streaminfo(stream)
            path = os.path.join(tmpdir, 'streams.json')
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666)
            f = os.fdopen(fd, 'w')
            json.dump(streams, f, indent=2, sort_keys=True)
            f.close()
            os.rename(tmpdir, nextdir)
            os.utime(nextdir, None)
            os.symlink(next_name, newlink)
            os.rename(newlink, symlink)
            del self.pending[stream]

        stream = PersistentStream(handle, tmpdir, setdir=setdir, commit=commit)
        self.pending[stream] = tmpdir
        return stream

    def _streaminfo(self, stream):
        return {'name': stream.name,
                'header': stream.handle.header,
                'streams': {x.name: self._streaminfo(x) for x in (stream.streams or {}).values()}}

    def load(self, setdir, node=None, nodename=None, default=()):
        assert bool(node) != bool(nodename)
        assert nodename != 'dataset'
        assert node.name != 'dataset'
        # TODO: handle substream fun
        name = nodename or self.name_by_node.get(node, node.name)
        nodedir = os.path.join(setdir, name)
        try:
            with open(os.path.join(nodedir, 'default-stream')) as f:
                msgs = node.schema.read_multiple_packed(f)
                return [Wrapper(x, None, setdir) for x in msgs]
        except IOError:
            if default is not ():
                return default
            raise
