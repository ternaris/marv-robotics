# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import heapq
import re
import sys
import warnings
from collections import defaultdict, namedtuple
from contextlib import ExitStack, contextmanager
from itertools import groupby
from logging import getLogger
from os import walk
from pathlib import Path

import capnp  # noqa: F401,TC002  pylint: disable=unused-import
from rosbags import rosbag1, rosbag2, serde
from rosbags.serde.messages import MSGDEFCACHE
from rosbags.typesys import get_types_from_idl, get_types_from_msg, register_types, types
from rosbags.typesys.msg import normalize_msgtype

import marv_api as marv
import marv_nodes
from marv_api import DatasetInfo, ReaderError

from .bag_capnp import Bagmeta, Message  # pylint: disable=import-error


class Baginfo(namedtuple('Baginfo', 'filename basename prefix timestamp idx')):

    @classmethod
    def parse(cls, filename):
        assert filename.endswith('.bag'), filename
        basename = filename[:-4]
        parts = basename.rsplit('_', 2)
        if parts[-1].isnumeric():
            idx = int(parts.pop())
        else:
            idx = None

        if re.match(r'\d{4}(?:-\d{2}){5}', parts[-1]):  # noqa: FS003
            timestamp = parts.pop()
        else:
            timestamp = None

        if parts:
            prefix = parts[0]
        else:
            prefix = None
        return cls(filename, basename, prefix, timestamp, idx)


def is_rosbag2(dirpath):
    metadata = dirpath / 'metadata.yaml'
    if not metadata.exists():
        return False

    content = metadata.read_text()
    return content.startswith('rosbag2_bagfile_information:')


def _scan_rosbag2(log, dirpath, dirnames, filenames):
    if not is_rosbag2(dirpath):
        return None

    try:
        reader = rosbag2.Reader(dirpath)
    except rosbag2.ReaderError as exc:
        log.warning('Rosbag2: %s %r', dirpath, exc)
        return None

    if dirnames:
        log.warning('Ignoring subdirectories of dataset %s: %r', dirpath, dirnames[:])
        dirnames[:] = []

        # Already created, we're only called because of ignored files
        if 'metadata.yaml' not in filenames:
            return None

    filenames = set(filenames)
    setfiles = {'metadata.yaml'} | {x.name for x in reader.paths}

    if extra := filenames - setfiles:
        log.warning('Ignoring files not listed in metadata.yaml %s: %r', dirpath, sorted(extra))

    if missing := setfiles - filenames:
        log.error(
            'Refusing to create rosbag2 dataset %s missing files: %r',
            dirpath,
            sorted(missing),
        )
        return None

    return DatasetInfo(dirpath.name, sorted(setfiles))


def _add_message_types(msgpath):
    typs = {}
    for root, dirnames, files in walk(msgpath):
        if '.rosbags_ignore' in files:
            dirnames.clear()
            continue
        dirnames.sort()
        for fname in sorted(files):
            path = Path(root, fname)
            if path.suffix == '.idl':
                typs.update(get_types_from_idl(path.read_text(encoding='utf-8')))
            elif path.suffix == '.msg':
                name = path.relative_to(path.parents[2]).with_suffix('')
                if '/msg/' not in str(name):
                    name = name.parent / 'msg' / name.name
                typs.update(get_types_from_msg(path.read_text(encoding='utf-8'), str(name)))
    register_types(typs)


def dirscan(dirpath, dirnames, filenames):
    """Scan for directories containing bags (ROS1 and ROS2).

    For rosbag2 datasets this scanner behaves identical to default :py:func:`scan` below.

    For ROS1 bag files it looks for directories containing at least one bag file and will create a
    dataset with all files contained, ignoring further subdirectories, including rosbag2 datasets;
    warnings are logged if any such subdirectories are ignored.

    """
    log = getLogger(f'{__name__}.dirscan')
    dirpath = Path(dirpath)
    dataset = _scan_rosbag2(log, dirpath, dirnames, filenames)
    if dataset:
        return [dataset]

    if not any(x.endswith('.bag') for x in filenames):
        return []

    if dirnames:
        log.warning('Ignoring subdirectories of dataset %s: %r', dirpath, dirnames[:])
        dirnames[:] = []

    return [DatasetInfo(dirpath.name, filenames)]


def scan(dirpath, dirnames, filenames):  # pylint: disable=unused-argument
    """Scan for sets of ROS bag files (ROS1 and ROS2).

    Find rosbag2 datasets and log warnings if they contain additional files, not listed in
    metadata.yaml

    The remainder is for sets of ROS1 bag files:

    Bags suffixed with a consecutive index are grouped into sets::

        foo_0.bag
        foo_1.bag
        foo_3.bag
        foo_4.bag

    results in::

        foo   [foo_0.bag, foo_1.bag]
        foo_3 [foo_3.bag]
        foo_4 [foo_4.bag]

    In this example the bag with index 2 is missing which results in
    foo_3 and foo_4 to be individual sets with one bag each.

    The timestamps used by ``rosbag record`` are stripped from the
    name given to sets, but are kept for the remaining individual sets
    in case a bag is missing::

        foo_2018-01-12-14-05-12_0.bag
        foo_2018-01-12-14-45-23_1.bag
        foo_2018-01-12-14-55-42_3.bag

    results in::

        foo [foo_2018-01-12-14-05-12_0.bag,
             foo_2018-01-12-14-45-23_1.bag]
        foo_2018-01-12-14-45-23_1 [foo_2018-01-12-14-45-23_1.bag]
        foo_2018-01-12-14-55-42_3 [foo_2018-01-12-14-55-42_3.bag]

    For more information on scanners see :any:`marv_api.scanner`.

    Args:
        dirpath (str): The path to the directory currently being
            scanned.
        dirnames (str): Sorted list of subdirectories of the directory
            currently being scanned.  Change this in-place to control
            further traversal.
        filenames (str): Sorted list of files within the directory
            currently being scanned.

    Returns:
        A list of :class:`marv_api.DatasetInfo` instances mapping
        set of files to dataset names.  Absolute filenames must
        start with :paramref:`.dirpath`, relative filenames are
        automatically prefixed with it.

    See :ref:`cfg_c_scanner` config key.

    """
    log = getLogger(f'{__name__}.scan')
    dataset = _scan_rosbag2(log, Path(dirpath), dirnames, filenames)
    if dataset:
        return [dataset]

    groups = groupby(
        [Baginfo.parse(x) for x in reversed(filenames) if x.endswith('.bag')],
        lambda x: x.prefix,
    )
    bags = []
    datasets = []
    for prefix, group in groups:
        group = list(group)
        prev_idx = None
        for bag in group:
            expected_idx = bag.idx if prev_idx is None else prev_idx - 1
            if bag.idx != expected_idx or \
               bags and (bags[0].timestamp is None) != (bag.timestamp is None):
                datasets[0:0] = [DatasetInfo(x.basename, [x.filename]) for x in bags]
                bags[:] = []
            bags.insert(0, bag)
            prev_idx = bag.idx
            if bag.idx == 0:
                datasets.insert(0, DatasetInfo(prefix or bag.timestamp, [x.filename for x in bags]))
                bags[:] = []
            elif bag.idx is None:
                assert len(bags) == 1, bags
                datasets.insert(0, DatasetInfo(bag.basename, [bag.filename]))
                bags[:] = []
        datasets[0:0] = [DatasetInfo(x.basename, [x.filename]) for x in bags]
        bags[:] = []
    return datasets


def _read_bagmeta2(path):
    reader = rosbag2.Reader(Path(path).parent)

    return {
        'start_time': reader.start_time,
        'end_time': reader.end_time,
        'duration': reader.duration,
        'msg_count': reader.message_count,
        'msg_types': sorted({x.msgtype for x in reader.topics.values()}),
        'topics': sorted(reader.topics.keys()),
        'connections': [
            {
                'topic': x['topic_metadata']['name'],
                'datatype': x['topic_metadata']['type'],
                'msg_count': x['message_count'],
                'serialization_format': x['topic_metadata']['serialization_format'],
            } for x in reader.metadata['topics_with_message_count']
        ],
    }


@contextmanager
def open_rosbag1(path):
    try:
        with rosbag1.Reader(path) as bag:
            yield bag
    except rosbag1.ReaderError:
        raise ReaderError(
            (
                f'Unindexed bag file: {path}\n'
                '  File was not copied in full or recording did not finish properly\n'
                '  Use `rosbag reindex` to index what is there.'
            ),
        ) from None


@marv.node(Bagmeta)
@marv.input('dataset', marv_nodes.dataset)
def bagmeta(dataset):
    """Extract meta information from bag file.

    In case of multiple connections for one topic, they are assumed to
    be all of the same message type and either all be latching or none.

    A topic's message type and latching mode, and a message type's
    md5sum are assumed not to change across split bags.
    """
    # pylint: disable=too-many-locals

    dataset = yield marv.pull(dataset)
    files = list(dataset.files)
    if metadatapath := next((x.path for x in files if x.path.endswith('metadata.yaml')), None):
        meta = _read_bagmeta2(metadatapath)
        if meta:
            yield marv.push(meta)
            return

    paths = [x.path for x in files if x.path.endswith('.bag')]

    bags = []
    start_time = sys.maxsize
    end_time = 0
    connections = {}
    for path in paths:
        with open_rosbag1(path) as bag:
            try:
                _start_time = int(bag.start_time)
                _end_time = int(bag.end_time)
            except ValueError:
                _start_time = sys.maxsize
                _end_time = 0

            start_time = _start_time if _start_time < start_time else start_time
            end_time = _end_time if _end_time > end_time else end_time

            _connections = [
                {
                    'topic': x.topic,
                    'datatype': x.msgtype,
                    'md5sum': x.md5sum,
                    'msg_def': x.msgdef,
                    'msg_count': len(x.indexes),
                    'latching': bool(x.latching),
                } for x in bag.connections.values()
            ]

            _start_time = _start_time if _start_time != sys.maxsize else 0
            bags.append(
                {
                    'start_time': _start_time,
                    'end_time': _end_time,
                    'duration': _end_time - _start_time,
                    'msg_count': sum(x['msg_count'] for x in _connections),
                    'connections': _connections,
                    'version': 200,
                },
            )

            for _con in _connections:
                key = (_con['topic'], _con['datatype'], _con['md5sum'])
                con = connections.get(key)
                if con:
                    con['msg_count'] += _con['msg_count']
                    con['latching'] = con['latching'] or _con['latching']
                else:
                    connections[key] = _con.copy()

    connections = sorted(
        connections.values(),
        key=lambda x: (x['topic'], x['datatype'], x['md5sum']),
    )
    start_time = start_time if start_time != sys.maxsize else 0
    yield marv.push(
        {
            'start_time': start_time,
            'end_time': end_time,
            'duration': end_time - start_time,
            'msg_count': sum(x['msg_count'] for x in bags),
            'msg_types': sorted({x['datatype'] for x in connections}),
            'topics': sorted({x['topic'] for x in connections}),
            'connections': connections,
            'bags': bags,
        },
    )


def read_messages(paths, topics=None, start_time=None, end_time=None, wipe_typesys=False):
    """Iterate chronologically raw BagMessage for topic from paths."""
    # pylint: disable=too-many-locals

    if wipe_typesys:
        backup = types.FIELDDEFS.copy()
        for key in list(types.FIELDDEFS.keys()):
            if key not in [
                'builtin_interfaces/msg/Time',
                'builtin_interfaces/msg/Duration',
                'std_msgs/msg/Header',
            ]:
                types.FIELDDEFS.pop(key)
        MSGDEFCACHE.clear()

    with ExitStack() as stack:
        if wipe_typesys:
            stack.callback(
                lambda:
                (types.FIELDDEFS.clear() or types.FIELDDEFS.update(backup) or MSGDEFCACHE.clear()),
            )
        bags = [stack.enter_context(open_rosbag1(path)) for path in paths]
        if wipe_typesys:
            typs = {}
            for bag in bags:
                for rconn in bag.connections.values():
                    typs.update(get_types_from_msg(rconn.msgdef, rconn.msgtype))
            register_types(typs)
        gens = [
            bag.messages(
                connections=[x for x in bag.connections.values() if x.topic in topics],
                start=start_time,
                stop=end_time,
            ) for bag in bags
        ]
        prev_time = 0
        for connection, time, data in heapq.merge(*gens, key=lambda x: x[1]):
            assert time >= prev_time, (repr(time), repr(prev_time))
            yield connection, time, data
            prev_time = time


@marv.node(Message, group='ondemand')
@marv.input('dataset', marv_nodes.dataset)
@marv.input('bagmeta', bagmeta)
def raw_messages(dataset, bagmeta):  # noqa: C901  # pylint: disable=redefined-outer-name,too-many-branches,too-many-statements
    """Stream messages from a set of bag files."""
    # pylint: disable=too-many-locals

    bagmeta, dataset = yield marv.pull_all(bagmeta, dataset)

    try:
        rosbag_path = Path(dataset.files[0].path).parent
        reader = rosbag2.Reader(rosbag_path)
        msgpath = rosbag_path / 'messages'
        if not msgpath.exists():
            try:
                msgpath = yield marv.get_resource_path('messages')
            except marv.ResourceNotFoundError:
                msgpath = None
        if msgpath and msgpath.exists():
            _add_message_types(msgpath)
    except rosbag2.ReaderError:
        reader = None

    connections = bagmeta.connections
    requested = yield marv.get_requested()

    # Selectors are:
    # - '/topic' -> one individual stream, no group
    # - '/topic1,/topic2' -> one group with two streams
    # - '*:sensor_msgs/Imu' -> one group with one stream per matching connection
    # - '*:sensor_msgs/Imu,*:sensor_msgs/msg/Imu'
    #    -> one group with one stream per matching connection

    individuals = []
    groups = []
    for name in (x.name for x in requested):
        if re.search(r'[:,]', name):
            groups.append(name)
        else:
            individuals.append(name)

    def make_header(topic):
        # TODO: topic with more than one type is not supported
        con = next((x for x in connections if x.topic == topic), None)
        # TODO: start/end_time per topic?
        return {
            'start_time': bagmeta.start_time,
            'end_time': bagmeta.end_time,
            'msg_count': con.msg_count if con else 0,
            'msg_type': con.datatype if con else '',
            'msg_type_def': con.msg_def if con else '',
            'msg_type_md5sum': con.md5sum if con else '',
            'rosbag2': reader is not None,
            'topic': topic,
        }

    deprecated_names = set()
    bytopic = defaultdict(list)
    for name in groups:
        topics = set()
        for selector in name.split(','):
            try:
                reqtop, reqtype = selector.split(':')
            except ValueError:
                reqtop, reqtype = selector, '*'
            if reqtype != '*':
                norm = normalize_msgtype(reqtype)
                if reqtype != norm:
                    deprecated_names.add((reqtype, norm))
                    reqtype = norm

            # TODO: topic with more than one type is not supported
            topics.update(
                con.topic
                for con in connections
                if reqtop in ('*', con.topic) and reqtype in ('*', con.datatype)
            )
        group = yield marv.create_group(name)
        for topic in sorted(topics):
            stream = yield group.create_stream(f'{name}.{topic}', **make_header(topic))
            bytopic[topic].append(stream)
        yield group.finish()

    for old, new in deprecated_names:
        warnings.warn(
            (
                f'marv.select: Change all occurrences of {old} to {new}.'
                ' Support for old ROS1 names will be removed in 21.12.0'
            ),
            FutureWarning,
        )

    bagtopics = bagmeta.topics
    for topic in individuals:
        stream = yield marv.create_stream(topic, **make_header(topic))
        if topic not in bagtopics:
            yield stream.finish()
        bytopic[topic].append(stream)

    if not bytopic:
        return

    if not reader:
        paths = [x.path for x in dataset.files if x.path.endswith('.bag')]
        # TODO: topic with more than one type is not supported
        for conn, timestamp, data in read_messages(paths, topics=list(bytopic), wipe_typesys=True):
            dct = {'data': data, 'timestamp': timestamp}
            for stream in bytopic[conn.topic]:
                yield stream.msg(dct)
        return

    with reader:
        connections = [x for x in reader.connections.values() if x.topic in bytopic]
        for conn, timestamp, data in reader.messages(connections=connections):
            dct = {'data': data, 'timestamp': timestamp}
            for stream in bytopic[conn.topic]:
                yield stream.msg(dct)


messages = raw_messages  # pylint: disable=invalid-name


def make_deserialize(stream):
    """Create appropriate deserialize function for rosbag1 and 2."""
    deserialize_cdr = serde.deserialize_cdr
    ros1_to_cdr = serde.ros1_to_cdr
    typename = stream.msg_type
    if stream.rosbag2:
        return lambda data: deserialize_cdr(data, typename)
    return lambda data: deserialize_cdr(ros1_to_cdr(data, typename), typename)


def get_float_seconds(stamp):
    """Get floating point seconds from ros1 and ros2 message header stamp."""
    if hasattr(stamp, 'to_sec'):
        return stamp.to_sec()
    return stamp.sec + stamp.nanosec * 1e-9


def make_get_timestamp(log, stream=None):
    """Make utitliy to get message header timestamp in nanoseconds.

    Falling back to bag message timestamp if header stamp is zero or unavailable.

    Args:
        log: logger instance
        stream: Obsolete, previously needed argument

    Returns:
        Function retrieving timestamp from message.

    """
    fallback = None

    if stream is not None:
        warnings.warn(
            (
                'Use make_get_timestamp(log) instead of make_get_timestamp(log, stream). '
                'Obsolete stream argument will be removed in 21.12.0'
            ),
            FutureWarning,
            stacklevel=1,
        )

    def stamp_to_nanosec(stamp):
        return stamp.sec * 10**9 + stamp.nanosec

    def get_timestamp(rosmsg, bagmsg):
        """Return header timestamp, falling back to bagmsg timestamp if zero or unavailable.

        Args:
            rosmsg: Deserialized ROS message
            bagmsg: Bag message as streamed by marv_robotics.bag.messages

        Returns:
            Message timestamp.

        """
        nonlocal fallback
        if fallback is None:
            if hasattr(rosmsg, 'header'):
                fallback = stamp_to_nanosec(rosmsg.header.stamp) == 0 and bagmsg.timestamp > 600e9
                if fallback:
                    log.warning('Header time is zero, will use message time instead.')
            else:
                fallback = True

        if fallback:
            return bagmsg.timestamp

        return stamp_to_nanosec(rosmsg.header.stamp)

    return get_timestamp
