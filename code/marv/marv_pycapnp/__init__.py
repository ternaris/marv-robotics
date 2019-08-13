# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import os
from collections.abc import Mapping, Sequence

from capnp.lib.capnp import _DynamicEnum
from capnp.lib.capnp import _DynamicListReader
from capnp.lib.capnp import _DynamicStructReader

from marv_node.setid import SetID


def _to_dict(value, field=None, field_type=None, which=False):
    if isinstance(value, _DynamicStructReader):
        schema = value.schema
        dct = {}
        for name in schema.non_union_fields:
            dct[name] = _to_dict(getattr(value, name), field=schema.fields[name], which=which)

        if schema.union_fields:
            _which = value.which()
            dct[_which] = _to_dict(getattr(value, _which), field=schema.fields[_which], which=which)
            if which:
                dct['_which'] = _which

        return dct

    if isinstance(value, _DynamicListReader):
        element_type = (field_type or field.proto.slot.type).list.elementType
        return [
            _to_dict(element, field_type=element_type, which=which) for element in value
        ]

    if isinstance(value, _DynamicEnum):
        return value._as_str()  # pylint: disable=protected-access

    return value


def _wrap(value, streamdir, setdir, field=None, field_type=None):
    if isinstance(value, _DynamicStructReader):
        return Wrapper(value, streamdir, setdir)

    if isinstance(value, _DynamicListReader):
        if field:
            element_type = field.proto.slot.type.list.elementType
        else:
            element_type = field_type.list.elementType
        return ListWrapper(value, element_type, streamdir, setdir)

    return value


class ListWrapper:
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
        return f"[{', '.join([repr(x) for x in self])}]"


class Wrapper:
    def __init__(self, struct_reader, streamdir, setdir):
        assert isinstance(struct_reader, _DynamicStructReader), type(struct_reader)
        self._reader = struct_reader
        self._streamdir = streamdir  # HACK: overloaded
        self._setdir = setdir
        self._storedir = None  # HACK: patched by compare

    # @property
    # def path(self):  # HACK: overload
    #     return os.path.realpath(os.path.join(self._streamdir, self.name))

    @property
    def relpath(self):  # HACK: overload
        path = os.path.relpath(self.path, self._setdir)
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
        store = Store(self._storedir, {node.name: node})
        return store.load(self._setdir, node, default=None)

    @classmethod
    def _unwrap(cls, data):
        unwrap = cls._unwrap
        if isinstance(data, Mapping):
            return {k: unwrap(v) for k, v in data.items()}

        if isinstance(data, Sequence) and not isinstance(data, (bytes, str)):
            return [unwrap(x) for x in data]

        if isinstance(data, Wrapper):
            return data._reader  # pylint: disable=protected-access

        return data

    def __getattr__(self, name):
        parts = name.split('_')
        field_name = parts[0] + ''.join(((x[0].upper() + x[1:]) if x else '_') for x in parts[1:])

        # pylint: disable=protected-access
        if field_name in self._reader.schema.fieldnames and self._reader._has(field_name):
            field = self._reader.schema.fields[field_name]
            return _wrap(getattr(self._reader, name), self._streamdir, self._setdir, field=field)

        if name == 'id' and self._reader._has('id0') and self._reader._has('id1'):
            return SetID(self._reader.id0, self._reader.id1)

        return getattr(self._reader, name)  # Not a field, but e.g. a method

    def __repr__(self):
        return f'<Wrapper {self._reader.schema.node.displayName}>'
