# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import rosbag


_get_start_time = rosbag.Bag.get_start_time
_get_end_time = rosbag.Bag.get_end_time


def get_start_time(self):
    """
    Returns the start time of the bag.
    @return: a timestamp of the start of the bag
    @rtype: float, timestamp in seconds, includes fractions of a second
    """
    if self._chunks:
        return min(x.start_time.to_sec() for x in self._chunks)
    return _get_start_time(self)


def get_end_time(self):
    """
    Returns the end time of the bag.
    @return: a timestamp of the end of the bag
    @rtype: float, timestamp in seconds, includes fractions of a second
    """
    if self._chunks:
        return max(x.end_time.to_sec() for x in self._chunks)
    return _get_end_time(self)


rosbag.Bag.get_start_time = get_start_time
rosbag.Bag.get_end_time = get_end_time
