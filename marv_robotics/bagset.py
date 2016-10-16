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

import logging
import os
import re
from collections import namedtuple
from itertools import groupby

import marv
import rosbag


Baginfo = namedtuple('Baginfo', ('prefix', 'idx', 'timestamp', 'bag'))
LOG = logging.getLogger(__name__)
PATTERN = '*.bag'


def make_baginfo(bag):
    """Make baginfo from fileinfo"""
    regex = r'(.+?)(?:_(\d{4}(?:-\d{2}){5})_(\d+))?.bag$'
    prefix, timestamp, idx = re.match(regex, bag.path).groups()
    if idx is not None:
        idx = int(idx)
    return Baginfo(prefix=prefix, idx=idx, timestamp=timestamp, bag=bag)


def scan(new_files):
    """Attempt to create filesets for new files"""
    baginfos = (make_baginfo(bag) for bag in reversed(sorted(new_files)))
    for _, baginfos in groupby(baginfos, lambda x: x.prefix):
        bags = []
        prev_idx = None
        for _, idx, _, bag in baginfos:
            LOG.debug('Considering idx=%r %r', idx, bag)
            expected_idx = idx if prev_idx is None else prev_idx - 1
            if idx != expected_idx:
                LOG.debug('Expected idx=%r discarding %r', expected_idx, bags)
                bags = []

            bags.insert(0, bag)
            prev_idx = idx

            if not idx:
                marv.make_fileset(bags)
                bags = []

        if bags:
            LOG.debug('Discarding unfinished %r', bags)


def read_messages(files, topics):
    for file in files:
        with rosbag.Bag(file.path) as bag:
            for msg in bag.read_messages(topics=topics):
                yield msg


@marv.node()
@marv.input('fileset')
def bagset_name(fileset):
    """Extract bagset name from file path"""
    name = make_baginfo(fileset.files[0]).prefix.rsplit(os.sep, 1)[1]
    return name


@marv.node(_ondemand=True)
@marv.input('fileset')
@marv.input('bagmeta')
@marv.param('filter', help='List of ORed filters for message topic:msgtype')
def messages(fileset, bagmeta, filter=('*:*',)):
    topics = None if '*:*' in filter else \
             [k for k, v in bagmeta.topics.iteritems()
              if any(('{}:{}'.format(x, y) in filter)
                     for x, y in [('*', v.msg_type),
                                  (k, '*'),
                                  (k, v.msg_type)])]
    return None if topics == [] else read_messages(fileset.files, topics)
