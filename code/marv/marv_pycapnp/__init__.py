# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import os
from collections import Mapping, Sequence

from capnp.lib.capnp import _DynamicEnum
from capnp.lib.capnp import _DynamicListReader
from capnp.lib.capnp import _DynamicStructReader
from flask import current_app

from marv_node.setid import SetID


def _to_dict(value, field=None, field_type=None, which=False):
    if isinstance(value, _DynamicStructReader):
        schema = value.schema
        dct = {}
        for name in schema.non_union_fields:
            dct[name] = _to_dict(getattr(value, name), field=schema.fields[name], which=which)

        if schema.union_fields:
            _which = str(value.which)
            dct[_which] = _to_dict(getattr(value, _which), field=schema.fields[_which], which=which)
            if which:
                dct['_which'] = _which

        return dct

    elif isinstance(value, _DynamicListReader):
        element_type = (field_type or field.proto.slot.type).list.elementType
        return [
            _to_dict(element, field_type=element_type, which=which) for element in value
        ]

    elif isinstance(value, str) and (field_type or field.proto.slot.type).which.raw == 12L:  # :Text
        return value.decode('utf-8')

    elif isinstance(value, _DynamicEnum):
        return value._as_str()

    return value


def _wrap(value, streamdir, setdir, field=None, field_type=None):
    if isinstance(value, _DynamicStructReader):
        return Wrapper(value, streamdir, setdir)

    elif isinstance(value, _DynamicListReader):
        element_type = field.proto.slot.type.list.elementType
        return ListWrapper(value, element_type, streamdir, setdir)

    elif isinstance(value, str) and (field_type or field.proto.slot.type).which.raw == 12L:  # :Text
        return value.decode('utf-8')

    return value


class ListWrapper(object):
    def __init__(self, list_reader, field_type, streamdir, setdir):
        assert isinstance(list_reader, _DynamicListReader), type(list_reader)
        self._field_type = field_type
        self._reader = list_reader
        self._streamdir = streamdir
        self._setdir = setdir

    def _wrap(self, item):
        return _wrap(item, self._streamdir, self._setdir, field_type=self._field_type)

    def __getitem__(self, idx):
        if isinstance(idx, slice):  # pycapnp can't handle slices
            return [self._wrap(x) for x in list(self._reader)[idx]]
        return self._wrap(self._reader[idx])

    def __eq__(self, other):
        return self[:] == other

    def __iter__(self):
        return (self._wrap(x) for x in self._reader)

    def __len__(self):
        return len(self._reader)

    def __repr__(self):
        return '[{}]'.format(', '.join([repr(x) for x in self]))


class Wrapper(object):
    def __init__(self, struct_reader, streamdir, setdir):
        assert isinstance(struct_reader, _DynamicStructReader), type(struct_reader)
        self._reader = struct_reader
        self._streamdir = streamdir  # HACK: overloaded
        self._setdir = setdir

    # @property
    # def path(self):  # HACK: overload
    #     return os.path.realpath(os.path.join(self._streamdir, self.name))

    @property
    def relpath(self):  # HACK: overload
        path = os.path.relpath(self.path.decode('utf-8'), self._setdir)
        return path.lstrip('.')

    @classmethod
    def from_dict(cls, schema, data):
        setid = data.pop('id', None)
        if isinstance(setid, SetID):
            data['id0'], data['id1'] = setid.lohi
        dct = cls._unwrap(data)
        struct_reader = schema.new_message(**dct).as_reader()
        return cls(struct_reader, None, None)

    def to_dict(self, which=None):
        return _to_dict(self._reader, which=which)

    def load(self, node):
        from marv_store import Store
        storedir = current_app.site.config.marv.storedir
        store = Store(storedir, {node.name: node})
        return store.load(self._setdir, node, default=None)

    @classmethod
    def _unwrap(cls, data):
        unwrap = cls._unwrap
        if isinstance(data, Mapping):
            return {k: unwrap(v) for k, v in data.iteritems()}
        elif isinstance(data, Sequence) and not isinstance(data, basestring):
            return [unwrap(x) for x in data]
        elif isinstance(data, Wrapper):
            return data._reader
        else:
            return data

    def __getattr__(self, name):
        parts = name.split('_')
        field_name = parts[0] + ''.join(((x[0].upper() + x[1:]) if x else '_') for x in parts[1:])

        if field_name in self._reader.schema.fieldnames and self._reader._has(field_name):
            field = self._reader.schema.fields[field_name]
            return _wrap(getattr(self._reader, name), self._streamdir, self._setdir, field=field)

        elif name == 'id' and self._reader._has('id0') and self._reader._has('id1'):
            return SetID(self._reader.id0, self._reader.id1)

        return getattr(self._reader, name)  # Not a field, but e.g. a method

    def __repr__(self):
        return '<Wrapper {}>'.format(self._reader.schema.node.displayName)
