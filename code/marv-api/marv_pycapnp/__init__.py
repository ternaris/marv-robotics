# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import json
from collections.abc import Mapping, Sequence
from itertools import dropwhile, islice
from pathlib import Path
from pickle import PickleBuffer

from capnp.lib.capnp import _DynamicEnum, _DynamicListReader, _DynamicStructReader
from ruamel.yaml import YAML

GETATTR_HOOKS = []


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
        self._streamdir = Path(streamdir) if streamdir else None
        self._setdir = Path(setdir) if setdir else None

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
    def __init__(self, struct_reader, streamdir, setdir, storedir=None):
        assert isinstance(struct_reader, _DynamicStructReader), type(struct_reader)
        self._reader = struct_reader
        self._streamdir = Path(streamdir) if streamdir else None
        self._setdir = Path(setdir) if setdir else None
        self._storedir = Path(storedir) if storedir else None

    def __reduce_ex__(self, protocol):
        if protocol < 5:
            raise RuntimeError('Needs at least pickle protocol 5')

        builder = self._reader.as_builder()
        protoname = builder.schema.node.displayName.replace('/', '.')\
                                                   .replace('.capnp:', '_capnp:')
        meta = {
            'protoname': protoname,
            'streamdir': str(self._streamdir),
            'setdir': str(self._setdir),
            'storedir': str(self._storedir),
        }
        segments = builder.to_segments()
        return (self.from_segments, (meta, *[PickleBuffer(x) for x in segments]))

    @property
    def userdata(self):
        """Return dataset user data from meta.json/.yaml userdata key.

        User data is read from a top-level 'userdata' key in either meta.json or meta.yaml
        searched for in that order among the dataset files.

        """
        if self._reader.schema.node.displayName != 'marv_nodes/types.capnp:Dataset':
            raise AttributeError('path')

        paths = [Path(x.path) for x in self.files]
        if meta := next((x for x in paths if x.name == 'meta.json'), None):
            # We can be called during local ingest before files are moved into
            # position.
            try:
                dct = json.loads(meta.read_text())
            except FileNotFoundError:
                return None
            return dct.get('userdata')

        meta = next((x for x in paths if x.name == 'meta.yaml'), None)
        # TODO: Waiting for https://github.com/ros2/rosbag2/issues/547
        # if meta is None:
        #     meta = next((x for x in paths if x.name == 'metadata.yaml'), None)
        if meta is None:
            return None

        # We can be called during local ingest before files are moved into
        # position.
        yaml = YAML(typ='safe')
        try:
            dct = yaml.load(meta.read_text())
        except FileNotFoundError:
            return None
        return dct.get('userdata')

    @property
    def path(self):
        """Absolute path string to access file during node run."""
        if self._reader.schema.node.displayName != 'marv_nodes/types.capnp:File':
            raise AttributeError('path')

        path = Path(self._reader.path)

        # File in scanroot
        if self._streamdir is None:
            return str(path)

        # FUTURE
        # if not path.is_absolute():
        #     return self._streamdir / path  # do we trust path?

        assert self._setdir
        if self._setdir not in path.parents or not path.exists():
            path = self._setdir / self._path_within_setdir(path)

        return str(path)

    @property
    def relpath(self):
        """Path string relative to setdir to reference files for the frontend."""
        if self._reader.schema.node.displayName != 'marv_nodes/types.capnp:File':
            raise AttributeError('relpath')

        # File in scanroot
        if self._streamdir is None:
            raise AttributeError('relpath')

        path = Path(self._reader.path)
        return str(self._path_within_setdir(path))

    def _path_within_setdir(self, path):
        # Path relative to setdir, no relative_to() to handle moved stores
        setid = self._setdir.name
        parts = list(islice(dropwhile(lambda x: x != setid, path.parts), 1, None))

        # Path to temporary streamdir during initial node run
        if parts[0][0] == '.':
            parts[0] = parts[0][1:]

        return Path(*parts)

    @classmethod
    def from_segments(cls, meta, *segments):
        from marv_api.utils import find_obj  # pylint: disable=import-outside-toplevel

        schema = find_obj(meta.pop('protoname'))
        struct_reader = schema.from_segments(segments)
        return cls(struct_reader, **meta)

    @classmethod
    def from_dict(cls, schema, data, setdir=None, streamdir=None):
        from marv_api.setid import SetID  # pylint: disable=import-outside-toplevel

        setid = data.pop('id', None)
        if isinstance(setid, SetID):
            data['id0'], data['id1'] = setid.lohi
        dct = cls._unwrap(data)
        struct_reader = schema.new_message(**dct).as_reader()
        return cls(struct_reader, streamdir, setdir)

    def to_dict(self, which=None):
        return _to_dict(self._reader, which=which)

    def load(self, node):
        from marv_store import Store  # pylint: disable=import-outside-toplevel
        store = Store(str(self._storedir), {node.name: node})
        return store.load(str(self._setdir), node, default=None)

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

    def __getattr__(self, name):  # noqa: C901  # pylint: disable=too-many-return-statements
        from marv_api.setid import SetID  # pylint: disable=import-outside-toplevel

        for hook in GETATTR_HOOKS:
            handled, ret = hook(self, self._reader.schema.node.displayName, name)
            if handled:
                return ret

        parts = name.split('_')
        field_name = parts[0] + ''.join(((x[0].upper() + x[1:]) if x else '_') for x in parts[1:])

        # pylint: disable=protected-access
        if field_name in self._reader.schema.fieldnames and self._reader._has(field_name):
            field = self._reader.schema.fields[field_name]
            value = getattr(self._reader, name)
            return _wrap(value, self._streamdir, self._setdir, field=field)

        if name == 'id' and self._reader._has('id0') and self._reader._has('id1'):
            return SetID(self._reader.id0, self._reader.id1)

        try:
            return getattr(self._reader, name)  # Not a field, but e.g. a method
        except AttributeError:
            raise AttributeError(name) from None

    def __repr__(self):
        return f'<Wrapper {self._reader.schema.node.displayName}>'
