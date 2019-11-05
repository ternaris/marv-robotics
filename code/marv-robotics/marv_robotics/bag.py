# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import re
import sys
from collections import defaultdict, namedtuple
from functools import reduce
from itertools import groupby

import capnp  # pylint: disable=unused-import

import marv
import marv_nodes
from marv.scanner import DatasetInfo
from marv_ros import genpy
from marv_ros import rosbag
from marv_ros.rosbag import _get_message_type
from .bag_capnp import Bagmeta, Header, Message  # pylint: disable=import-error


# Regular expression used to aggregate individual bags into sets (see
# below). Bags with the same *name* and consecutive *idx* starting
# with 0 are put into sets. If one bag is missing all remaining bags
# will result in sets with one bag each.
REGEX = re.compile(r"""
^
(?P<basename>
  (?P<name>
    .+?
  )
  (?:
    _(?P<timestamp>
      \d{4}(?:-\d{2}){5}
    )
  )?
  (?:
    _(?P<idx>
      \d+
    )
  )?
)
.bag$
""", re.VERBOSE)


class Baginfo(namedtuple('Baginfo', 'filename basename name timestamp idx')):
    def __new__(cls, filename, basename, name, timestamp=None, idx=None):
        # pylint: disable=too-many-arguments
        idx = None if idx is None else int(idx)
        return super(Baginfo, cls).__new__(cls, filename, basename,
                                           name, timestamp, idx)


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

    For more information on scanners see :any:`marv.scanner`.

    Args:
        dirpath (str): The path to the directory currently being
            scanned.
        dirnames (str): Sorted list of subdirectories of the directory
            currently being scanned.  Change this in-place to control
            further traversal.
        filenames (str): Sorted list of files within the directory
            currently being scanned.

    Returns:
        A list of :class:`marv.scanner.DatasetInfo` instances mapping
        set of files to dataset names.  Absolute filenames must
        start with :paramref:`.dirpath`, relative filenames are
        automatically prefixed with it.

    See :ref:`cfg_c_scanner` config key.

    """
    groups = groupby([Baginfo(x, **re.match(REGEX, x).groupdict())
                      for x in reversed(filenames)
                      if x.endswith('.bag')],
                     lambda x: x.name)
    bags = []
    datasets = []
    for name, group in groups:
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
                datasets.insert(0, DatasetInfo(name, [x.filename for x in bags]))
                bags[:] = []
            elif bag.idx is None:
                assert len(bags) == 1, bags
                datasets.insert(0, DatasetInfo(bag.basename, [bag.filename]))
                bags[:] = []
        datasets[0:0] = [DatasetInfo(x.basename, [x.filename]) for x in bags]
        bags[:] = []
    return datasets


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
    paths = [x.path for x in dataset.files if x.path.endswith('.bag')]

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
        next_key = reduce(lambda x, y: x if x[0] < y[0] else y, msgs.items())[0]
        next_time, next_msg = msgs.pop(next_key)
        assert next_time >= prev_time
        yield next_msg
        prev_time = next_time


@marv.node(Message, Header, group='ondemand')
@marv.input('dataset', marv_nodes.dataset)
@marv.input('bagmeta', bagmeta)
def raw_messages(dataset, bagmeta):  # pylint: disable=redefined-outer-name
    """Stream messages from a set of bag files."""
    # pylint: disable=too-many-locals

    bagmeta, dataset = yield marv.pull_all(bagmeta, dataset)
    bagtopics = bagmeta.topics
    connections = bagmeta.connections
    paths = [x.path for x in dataset.files if x.path.endswith('.bag')]
    requested = yield marv.get_requested()

    alltopics = set()
    bytopic = defaultdict(list)
    groups = {}
    for name in [x.name for x in requested if ':' in x.name]:
        reqtop, reqtype = name.split(':')
        # BUG: topic with more than one type is not supported
        topics = [
            con.topic for con in connections
            if reqtop in ('*', con.topic) and reqtype in ('*', con.datatype)
        ]
        group = groups[name] = yield marv.create_group(name)
        create_stream = group.create_stream

        for topic in topics:
            # BUG: topic with more than one type is not supported
            # pylint: disable=stop-iteration-return
            con = next(x for x in connections if x.topic == topic)
            # TODO: start/end_time per topic?
            header = {'start_time': bagmeta.start_time,
                      'end_time': bagmeta.end_time,
                      'msg_count': con.msg_count,
                      'msg_type': con.datatype,
                      'msg_type_def': con.msg_def,
                      'msg_type_md5sum': con.md5sum,
                      'topic': topic}
            stream = yield create_stream(topic, **header)
            bytopic[topic].append(stream)
        alltopics.update(topics)
        if group:
            yield group.finish()

    for topic in [x.name for x in requested if ':' not in x.name]:
        if topic in alltopics:
            continue

        # BUG: topic with more than one type is not supported
        con = next((x for x in connections if x.topic == topic), None)
        # TODO: start/end_time per topic?
        header = {'start_time': bagmeta.start_time,
                  'end_time': bagmeta.end_time,
                  'msg_count': con.msg_count if con else 0,
                  'msg_type': con.datatype if con else '',
                  'msg_type_def': con.msg_def if con else '',
                  'msg_type_md5sum': con.md5sum if con else '',
                  'topic': topic}
        stream = yield marv.create_stream(topic, **header)
        if topic not in bagtopics:
            yield stream.finish()
        bytopic[topic].append(stream)
        alltopics.add(topic)

    if not alltopics:
        return

    # BUG: topic with more than one type is not supported
    for topic, raw, timestamp in read_messages(paths, topics=list(alltopics)):
        dct = {'data': raw[1], 'timestamp': timestamp.to_nsec()}
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
