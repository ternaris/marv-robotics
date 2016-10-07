# -*- coding: utf-8 -*-
#
# This file is part of MARV Robotics
#
# Copyright 2016 Ternaris
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function

from datetime import datetime
import marv
import rosbag


def to_dict(value):
    try:
        value = value._asdict()
    except AttributeError:
        pass

    if isinstance(value, dict):
        return {k: to_dict(v) for k, v in value.items()}
    else:
        return value


@marv.node()
@marv.input('fileset')
def bagmeta(fileset):
    bags = []
    for file in fileset.files:
        with rosbag.Bag(file.path) as bag:
            start_time = datetime.fromtimestamp(bag.get_start_time())
            end_time = datetime.fromtimestamp(bag.get_end_time())
            duration = end_time - start_time
            bags.append({
                'compression_info': to_dict(bag.get_compression_info()),
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'message_count': bag.get_message_count(),
                'type_and_topic_info': to_dict(bag.get_type_and_topic_info()),
                'version': bag.version,
                'connections': {k: v.__dict__ for k, v in bag._connections.items()},
            })

    msg_types = {}
    topics = {}
    for bag in bags:
        msg_types.update(bag['type_and_topic_info']['msg_types'])
        for k, v in bag['type_and_topic_info']['topics'].items():
            if k not in topics:
                topics[k] = {'message_count': v['message_count'],
                             'msg_type': v['msg_type']}
            else:
                topics[k]['message_count'] += v['message_count']

    meta = {
        'start_time': bags[0]['start_time'],
        'end_time': bags[-1]['end_time'],
        'duration': bags[-1]['end_time'] - bags[0]['start_time'],
        'message_count': sum(x['message_count'] for x in bags),
        'topics': topics,
        'msg_types': msg_types,
        'bags': bags,
    }
    return meta
