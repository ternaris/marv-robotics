# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import re
import sys
from collections import defaultdict, namedtuple
from itertools import groupby
from pathlib import Path

import capnp  # pylint: disable=unused-import
import yaml

import marv_api as marv
import marv_nodes
from marv_api import DatasetInfo
from marv_ros import genpy
from marv_ros import rosbag
from marv_ros.rosbag import _get_message_type
from .bag_capnp import Bagmeta, Message  # pylint: disable=import-error

try:
    import rosbag2_py as rosbag2
except ImportError:
    rosbag2 = None

if rosbag2 is not None:
    from rclpy.serialization import deserialize_message  # pylint: disable=import-error
    from rosidl_runtime_py.utilities import get_message  # pylint: disable=import-error


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

        if re.match(r'\d{4}(?:-\d{2}){5}', parts[-1]):
            timestamp = parts.pop()
        else:
            timestamp = None

        if parts:
            prefix = parts[0]
        else:
            prefix = None
        return cls(filename, basename, prefix, timestamp, idx)


def _scan_rosbag2(dirpath, filenames):
    if 'metadata.yaml' not in filenames:
        return None

    dirpath = Path(dirpath)
    dct = yaml.safe_load((dirpath / 'metadata.yaml').read_text())
    try:
        info = dct['rosbag2_bagfile_information']
    except KeyError:
        return None

    return DatasetInfo(dirpath.name, ['metadata.yaml'] + info['relative_file_paths'])


def scan(dirpath, dirnames, filenames):  # pylint: disable=unused-argument
    """Scan for sets of ROS bag files.

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
    dataset = _scan_rosbag2(dirpath, filenames)
    if dataset:
        dirnames[:] = []
        return [dataset]

    groups = groupby([Baginfo.parse(x) for x in reversed(filenames) if x.endswith('.bag')],
                     lambda x: x.prefix)
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
    dct = yaml.safe_load(Path(path).read_text())
    try:
        info = dct['rosbag2_bagfile_information']
    except KeyError:
        return None
    start_time = info['starting_time']['nanoseconds_since_epoch']
    duration = info['duration']['nanoseconds']
    connections = [
        {'topic': x['topic_metadata']['name'],
         'datatype': x['topic_metadata']['type'],
         'msg_count': x['message_count'],
         'serialization_format': x['topic_metadata']['serialization_format']}
        for x in info['topics_with_message_count']
    ]
    return {
        'start_time': start_time,
        'end_time': start_time + duration,
        'duration': duration,
        'msg_count': info['message_count'],
        'msg_types': sorted({x['datatype'] for x in connections}),
        'topics': sorted({x['topic'] for x in connections}),
        'connections': connections,
    }


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
    files = dataset.files[:]
    if files[0].path.endswith('metadata.yaml'):
        meta = _read_bagmeta2(files[0].path)
        if meta:
            yield marv.push(meta)
            return

    paths = [x.path for x in files if x.path.endswith('.bag')]

    bags = []
    start_time = sys.maxsize
    end_time = 0
    connections = {}
    for path in paths:
        with rosbag.Bag(path) as bag:
            try:
                _start_time = int(bag.get_start_time() * 1.e9)
                _end_time = int(bag.get_end_time() * 1.e9)
            except rosbag.ROSBagException:
                _start_time = sys.maxsize
                _end_time = 0

            start_time = _start_time if _start_time < start_time else start_time
            end_time = _end_time if _end_time > end_time else end_time

            _msg_counts = defaultdict(int)
            for chunk in bag._chunks:  # pylint: disable=protected-access
                for conid, count in chunk.connection_counts.items():
                    _msg_counts[conid] += count

            _connections = [
                {'topic': x.topic,
                 'datatype': x.datatype,
                 'md5sum': x.md5sum,
                 'msg_def': x.msg_def,
                 'msg_count': _msg_counts[x.id],
                 'latching': bool(int(x.header.get('latching', 0)))}
                for x in bag._connections.values()  # pylint: disable=protected-access
            ]

            _start_time = _start_time if _start_time != sys.maxsize else 0
            bags.append({
                'start_time': _start_time,
                'end_time': _end_time,
                'duration': _end_time - _start_time,
                'msg_count': sum(_msg_counts.values()),
                'connections': _connections,
                'version': bag.version,
            })

            for _con in _connections:
                key = (_con['topic'], _con['datatype'], _con['md5sum'])
                con = connections.get(key)
                if con:
                    con['msg_count'] += _con['msg_count']
                    con['latching'] = con['latching'] or _con['latching']
                else:
                    connections[key] = _con.copy()

    connections = sorted(connections.values(),
                         key=lambda x: (x['topic'], x['datatype'], x['md5sum']))
    start_time = start_time if start_time != sys.maxsize else 0
    yield marv.push({
        'start_time': start_time,
        'end_time': end_time,
        'duration': end_time - start_time,
        'msg_count': sum(x['msg_count'] for x in bags),
        'msg_types': sorted({x['datatype'] for x in connections}),
        'topics': sorted({x['topic'] for x in connections}),
        'connections': connections,
        'bags': bags,
    })


def read_messages(paths, topics=None, start_time=None, end_time=None):
    """Iterate chronologically raw BagMessage for topic from paths."""
    bags = {path: rosbag.Bag(path) for path in paths}
    gens = {
        path: bag.read_messages(topics=topics, start_time=start_time, end_time=end_time, raw=True)
        for path, bag in bags.items()
    }
    msgs = {}
    prev_time = genpy.Time(0)
    while True:
        for key in gens.keys() - msgs.keys():
            try:
                msgs[key] = next(gens[key])
            except StopIteration:
                bags[key].close()
                del bags[key]
                del gens[key]
        if not msgs:
            break
        next_key = min(msgs.items(), key=lambda x: x[1][0])[0]
        next_time, next_msg = msgs.pop(next_key)
        assert next_time >= prev_time, (repr(next_time), repr(prev_time))
        yield next_msg
        prev_time = next_time


@marv.node(Message, group='ondemand')
@marv.input('dataset', marv_nodes.dataset)
@marv.input('bagmeta', bagmeta)
def raw_messages(dataset, bagmeta):  # noqa: C901  # pylint: disable=redefined-outer-name,too-many-branches,too-many-statements
    """Stream messages from a set of bag files."""
    # pylint: disable=too-many-locals

    bagmeta, dataset = yield marv.pull_all(bagmeta, dataset)

    rosbag2_metayaml = Path(dataset.files[0].path)
    if rosbag2_metayaml.name != 'metadata.yaml':
        rosbag2_metayaml = False

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
        return {'start_time': bagmeta.start_time,
                'end_time': bagmeta.end_time,
                'msg_count': con.msg_count if con else 0,
                'msg_type': con.datatype if con else '',
                'msg_type_def': con.msg_def if con else '',
                'msg_type_md5sum': con.md5sum if con else '',
                'rosbag2': bool(rosbag2_metayaml),
                'topic': topic}

    bytopic = defaultdict(list)
    for name in groups:
        topics = []
        for selector in name.split(','):
            try:
                reqtop, reqtype = selector.split(':')
            except ValueError:
                reqtop, reqtype = selector, '*'
            # TODO: topic with more than one type is not supported
            topics.extend(
                con.topic for con in connections
                if reqtop in ('*', con.topic) and reqtype in ('*', con.datatype)
            )
        group = yield marv.create_group(name)
        for topic in topics:
            stream = yield group.create_stream(f'{name}.{topic}', **make_header(topic))
            bytopic[topic].append(stream)
        yield group.finish()

    bagtopics = bagmeta.topics
    for topic in individuals:
        stream = yield marv.create_stream(topic, **make_header(topic))
        if topic not in bagtopics:
            yield stream.finish()
        bytopic[topic].append(stream)

    if not bytopic:
        return

    if not rosbag2_metayaml:
        paths = [x.path for x in dataset.files if x.path.endswith('.bag')]
        # TODO: topic with more than one type is not supported
        for topic, raw, timestamp in read_messages(paths, topics=list(bytopic)):
            dct = {'data': raw[1], 'timestamp': timestamp.to_nsec()}
            for stream in bytopic[topic]:
                yield stream.msg(dct)
        return

    meta = yaml.safe_load(rosbag2_metayaml.read_text())['rosbag2_bagfile_information']

    # TODO: workaround for older rosbag2 format versions
    if meta['version'] < 4:
        assert len(meta['relative_file_paths']) == 1
        uri = str(rosbag2_metayaml.parent / meta['relative_file_paths'][0])
    else:
        uri = str(rosbag2_metayaml.parent)

    storage_options = rosbag2.StorageOptions()
    storage_options.uri = uri
    storage_options.storage_id = meta['storage_identifier']

    reader = rosbag2.SequentialReader()
    reader.open(storage_options, rosbag2.ConverterOptions())

    storage_filter = rosbag2.StorageFilter()
    storage_filter.topics = list(bytopic)
    reader.set_filter(storage_filter)

    while reader.has_next():
        (topic, data, timestamp) = reader.read_next()
        dct = {'data': data, 'timestamp': timestamp}
        for stream in bytopic[topic]:
            yield stream.msg(dct)


messages = raw_messages  # pylint: disable=invalid-name

_ConnectionInfo = namedtuple('_ConnectionInfo', 'md5sum datatype msg_def')


def get_message_type(stream):
    """ROS message type from definition stored for stream."""
    if stream.msg_type and stream.msg_type_def and stream.msg_type_md5sum:
        info = _ConnectionInfo(md5sum=stream.msg_type_md5sum,
                               datatype=stream.msg_type,
                               msg_def=stream.msg_type_def)
        return _get_message_type(info)
    return None


def make_deserialize(stream):
    """Create appropriate deserialize function for rosbag1 and 2."""
    if stream.rosbag2:
        if rosbag2 is None:
            raise RuntimeError('rosbag2_py is needed to process rosbag2')

        pytype = get_message(stream.msg_type)

        def deserialize_ros2(data):
            return deserialize_message(data, pytype)

        return deserialize_ros2

    pytype = get_message_type(stream)
    if pytype is None:
        raise marv.Abort()

    def deserialize_ros1(data):
        rosmsg = pytype()
        rosmsg.deserialize(data)
        return rosmsg

    return deserialize_ros1


def get_float_seconds(stamp):
    """Get floating point seconds from ros1 and ros2 message header stamp."""
    if hasattr(stamp, 'to_sec'):
        return stamp.to_sec()
    return stamp.sec + stamp.nanosec * 1e-9
