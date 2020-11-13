# Copyright 2020  Ternaris.
# SPDX-License-Identifier: Apache-2.0

"""Simple rosbag2 reader and message deserializer."""

import sqlite3
import sys
from contextlib import contextmanager
from enum import IntEnum
from pathlib import Path
from struct import Struct, unpack
from tempfile import TemporaryDirectory
from typing import Any, Dict, Generator, Iterable, List, NamedTuple, Optional, Tuple, Union

import numpy  # type: ignore
import zstandard  # type: ignore
from ruamel.yaml import YAML, parser  # type: ignore

from . import types


class ReaderError(Exception):
    """Reader Error."""


class Valtype(IntEnum):
    """Msg field value types."""

    BASE = 1
    MESSAGE = 2
    ARRAY = 3
    SEQUENCE = 4


class Descriptor(NamedTuple):
    """Value type descriptor."""

    valtype: Valtype
    args: Any  # Union[Descriptor, Msgdef, Tuple[int, Descriptor], str]


class Field(NamedTuple):
    """Metadata of a field."""

    name: str
    descriptor: Descriptor


class Msgdef(NamedTuple):
    """Metadata of a message."""

    name: str
    fields: List[Field]
    cls: Any


Array = Union[List[Union[Msgdef, str]], numpy.ndarray]
BasetypeMap = Dict[str, Tuple[Any, int]]
MSGDEFCACHE: Dict[str, Msgdef] = {}
BASETYPEMAP_LE: BasetypeMap = {
    'bool': (Struct('?'), 1),
    'int8': (Struct('b'), 1),
    'int16': (Struct('<h'), 2),
    'int32': (Struct('<i'), 4),
    'int64': (Struct('<q'), 8),
    'uint8': (Struct('B'), 1),
    'uint16': (Struct('<H'), 2),
    'uint32': (Struct('<I'), 4),
    'uint64': (Struct('<Q'), 8),
    'float32': (Struct('<f'), 4),
    'float64': (Struct('<d'), 8),
}
BASETYPEMAP_BE: BasetypeMap = {
    'bool': (Struct('?'), 1),
    'int8': (Struct('b'), 1),
    'int16': (Struct('>h'), 2),
    'int32': (Struct('>i'), 4),
    'int64': (Struct('>q'), 8),
    'uint8': (Struct('B'), 1),
    'uint16': (Struct('>H'), 2),
    'uint32': (Struct('>I'), 4),
    'uint64': (Struct('>Q'), 8),
    'float32': (Struct('>f'), 4),
    'float64': (Struct('>d'), 8),
}
BASETYPES = set(BASETYPEMAP_LE.keys()) | {'string'}


def get_msgdef(typename: str) -> Msgdef:
    """Retrieve message definition for typename.

    Message definitions are cached globally and generated as needed.

    Args:
        typename: Msgdef type name to load.

    Returns:
        Message definition.

    """
    if typename not in MSGDEFCACHE:
        entries = types.FIELDDEFS[typename]

        def fixup(entry):
            if entry[0] == Valtype.BASE:
                return Descriptor(Valtype.BASE, entry[1])
            if entry[0] == Valtype.MESSAGE:
                return Descriptor(Valtype.MESSAGE, get_msgdef(entry[1]))
            if entry[0] == Valtype.ARRAY:
                return Descriptor(Valtype.ARRAY, (entry[1], fixup(entry[2])))
            if entry[0] == Valtype.SEQUENCE:
                return Descriptor(Valtype.SEQUENCE, fixup(entry[1]))
            raise ReaderError(  # pragma: no cover
                f'Unknown field type {entry[0]!r} encountered.',
            )

        MSGDEFCACHE[typename] = Msgdef(typename,
                                       [Field(name, fixup(desc)) for name, desc in entries],
                                       getattr(types, typename.replace('/', '__')))
    return MSGDEFCACHE[typename]


def deserialize_number(rawdata: bytes, bmap: BasetypeMap, pos: int, basetype: str) \
        -> Tuple[Union[bool, float, int], int]:
    """Deserialize a single boolean, float, or int.

    Args:
        rawdata: Serialized data.
        bmap: Basetype metadata.
        pos: Read position.
        basetype: Number type string.

    Returns:
        Deserialized number and new read position.

    """
    dtype, size = bmap[basetype]
    if pos % size:
        pos = pos + size - pos % size

    return dtype.unpack_from(rawdata, pos)[0], pos + size


def deserialize_string(rawdata: bytes, bmap: BasetypeMap, pos: int) \
        -> Tuple[str, int]:
    """Deserialize a string value.

    Args:
        rawdata: Serialized data.
        bmap: Basetype metadata.
        pos: Read position.

    Returns:
        Deserialized string and new read position.

    """
    if pos % 4:
        pos = pos + 4 - pos % 4
    length = bmap['int32'][0].unpack_from(rawdata, pos)[0]
    string = bytes(rawdata[pos + 4:pos + 4 + length - 1]).decode()
    return string, pos + 4 + length


def deserialize_array(rawdata: bytes, bmap: BasetypeMap, pos: int, num: int, desc: Descriptor) \
        -> Tuple[Array, int]:
    """Deserialize an array of items of same type.

    Args:
        rawdata: Serialized data.
        bmap: Basetype metadata.
        pos: Read position.
        num: Number of elements.
        desc: Element type descriptor.

    Returns:
        Deserialized array and new read position.

    """
    if desc.valtype == Valtype.BASE:
        if desc.args == 'string':
            strs = []
            while (num := num - 1) >= 0:
                val, pos = deserialize_string(rawdata, bmap, pos)
                strs.append(val)
            return strs, pos

        ndarr = numpy.frombuffer(rawdata, dtype=desc.args, count=num, offset=pos)
        if (bmap is BASETYPEMAP_LE) != (sys.byteorder == 'little'):
            ndarr = ndarr.byteswap()  # no inplace on readonly array
        return ndarr, pos + num * bmap[desc.args][1]

    if desc.valtype == Valtype.MESSAGE:
        msgs = []
        while (num := num - 1) >= 0:
            msg, pos = deserialize_message(rawdata, bmap, pos, desc.args)
            msgs.append(msg)
        return msgs, pos

    raise ReaderError(f'Nested arrays {desc!r} are not supported.')  # pragma: no cover


def deserialize_message(rawdata: bytes, bmap: BasetypeMap, pos: int, msgdef: Msgdef) \
        -> Tuple[Msgdef, int]:
    """Deserialize a message.

    Args:
        rawdata: Serialized data.
        bmap: Basetype metadata.
        pos: Read position.
        msgdef: Message definition.

    Returns:
        Deserialized message and new read position.

    """
    values: List[Any] = []

    for _, desc in msgdef.fields:
        if desc.valtype == Valtype.MESSAGE:
            obj, pos = deserialize_message(rawdata, bmap, pos, desc.args)
            values.append(obj)

        elif desc.valtype == Valtype.BASE:
            if desc.args == 'string':
                val, pos = deserialize_string(rawdata, bmap, pos)
                values.append(val)
            else:
                num, pos = deserialize_number(rawdata, bmap, pos, desc.args)
                values.append(num)

        elif desc.valtype == Valtype.ARRAY:
            arr, pos = deserialize_array(rawdata, bmap, pos, *desc.args)
            values.append(arr)

        elif desc.valtype == Valtype.SEQUENCE:
            size, pos = deserialize_number(rawdata, bmap, pos, 'int32')
            arr, pos = deserialize_array(rawdata, bmap, pos, int(size), desc.args)
            values.append(arr)

        else:  # pragma: no cover
            raise ReaderError(
                f'Could not deserialize unsupported Descriptor {desc!r}.',
            )

    return msgdef.cls(*values), pos


def deserialize(rawdata: bytes, typename: str) -> Msgdef:
    """Deserialize raw data into a message object.

    Args:
        rawdata: Serialized data.
        typename: Type to deserialize.

    Returns:
        Deserialized message object.

    """
    _, is_little = unpack('BB', rawdata[:2])

    msgdef = get_msgdef(typename)
    obj, _ = deserialize_message(rawdata[4:], BASETYPEMAP_LE if is_little else BASETYPEMAP_BE, 0,
                                 msgdef)
    return obj


@contextmanager
def decompress(path: Path, do_decompress: bool):
    """Transparent rosbag2 database decompression context.

    This context manager will yield a path to the decompressed file contents if do_compress==True,
    or the give path itself otherwise.

    Args:
        path: Potentially compressed file.
        do_decompress: Flag indicating if decompression shall occur.

    """
    if do_decompress:
        decomp = zstandard.ZstdDecompressor()
        with TemporaryDirectory() as tempdir:
            dbfile = Path(tempdir, path.stem)
            with path.open('rb') as infile, dbfile.open('wb') as outfile:
                decomp.copy_stream(infile, outfile)
                yield dbfile
    else:
        yield path


class Reader:
    """Rosbag2 reader.

    This class supports reading rosbag2 files. It implements all necessary features to access
    metadata and message steam.

    Version history:

        - Version 1: Initial format.
        - Version 2: Changed field sizes in C++ implementation.
        - Version 3: Added compression.
        - Version 4: Added QoS metadata to topics, changed relative file paths

    """

    def __init__(self, path: Union[Path, str]):  # noqa: C901
        """Open rosbag and check metadata.

        Args:
            path: Filesystem path to bag.

        """
        path = Path(path)
        try:
            yaml = YAML(typ='safe')
            yamlpath = path / 'metadata.yaml'
            dct = yaml.load(yamlpath.read_text())
        except FileNotFoundError:
            raise ReaderError(f'Could not find metadata at {yamlpath}.') from None
        except PermissionError:
            raise ReaderError(f'Could not read {yamlpath}.') from None
        except parser.ParserError as exc:
            raise ReaderError(f'Could not load YAML from {yamlpath}: {exc}') from None

        try:
            self.metadata = dct['rosbag2_bagfile_information']
            if (ver := self.metadata['version']) > 4:
                raise ReaderError(f'Rosbag2 version {ver} not supported; please report issue.')
            if storageid := self.metadata['storage_identifier'] != 'sqlite3':
                raise ReaderError(f'Rosbag2 storage plugin {storageid!r} not supported; '
                                  'please report issue.')

            basepath = path if ver >= 4 else path.parent
            self.paths = [basepath / x for x in self.metadata['relative_file_paths']]
            missing = [x for x in self.paths if not x.exists()]
            if missing:
                raise ReaderError(f'Some database files are missing: {[str(x) for x in missing]!r}')

            topics = [x['topic_metadata'] for x in self.metadata['topics_with_message_count']]
            noncdr = {y for x in topics if (y := x['serialization_format']) != 'cdr'}
            if noncdr:
                raise ReaderError('Serialization format(s) {noncdr!r} is not supported.')
            self.topics = {x['name']: x['type'] for x in topics}

            if self.compression_mode and (cfmt := self.compression_format) != 'zstd':
                raise ReaderError(f'Compression format {cfmt!r} is not supported')
        except KeyError as exc:
            raise ReaderError(f'A metadata key is missing {exc!r}') from None

    @property
    def duration(self) -> int:
        """Duration between earliest and latest messages."""
        return self.metadata['duration']['nanoseconds']

    @property
    def starting_time(self) -> int:
        """Timestamp of the earliest message."""
        return self.metadata['starting_time']['nanoseconds_since_epoch']

    @property
    def message_count(self) -> int:
        """Total message count."""
        return self.metadata['message_count']

    @property
    def compression_format(self) -> Optional[str]:
        """Compression format."""
        return self.metadata.get('compression_format', None) or None

    @property
    def compression_mode(self) -> Optional[str]:
        """Compression mode."""
        mode = self.metadata.get('compression_mode', '').lower()
        return mode if mode != 'none' else None

    def messages(self, topics: Iterable[str] = ()) \
            -> Generator[Tuple[str, str, int, bytes], None, None]:
        """Read messages from bag.

        Args:
            topics (optional): Iterable with topic names to filter for. An empty iterable yields
                all messages.

        Yields:
            Tuples of topic name, type, timestamp, and rawdata.

        """
        topics = tuple(topics)
        for filepath in self.paths:
            with decompress(filepath, self.compression_mode == 'file') as path:
                conn = sqlite3.connect(f'file:{path}?immutable=1', uri=True)
                conn.row_factory = lambda _, x: x
                cur = conn.cursor()
                cur.execute('SELECT count(*) FROM sqlite_master '
                            'WHERE type="table" AND name IN ("messages", "topics")')
                if cur.fetchone()[0] != 2:
                    raise ReaderError(f'Cannot open database {path} or database missing tables.')

                if topics:
                    cur.execute('SELECT topics.name,topics.type,messages.timestamp,messages.data '
                                'FROM messages JOIN topics ON messages.topic_id=topics.id '
                                f'WHERE topics.name IN ({",".join("?" for _ in topics)}) '
                                'ORDER BY timestamp', topics)
                else:
                    cur.execute('SELECT topics.name,topics.type,messages.timestamp,messages.data '
                                'FROM messages JOIN topics ON messages.topic_id=topics.id '
                                'ORDER BY timestamp')

                if self.compression_mode == 'message':
                    decomp = zstandard.ZstdDecompressor().decompress
                    for row in cur:
                        topic, msgtype, timestamp, data = row
                        yield topic, msgtype, timestamp, decomp(data)
                else:
                    yield from cur
