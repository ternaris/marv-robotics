# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from unittest.mock import Mock

from marv_robotics.bag import make_get_timestamp


def test_make_get_timestamp():
    # ROS2 no header
    log = Mock([])
    stream = Mock([], rosbag2=True)
    get_timestamp = make_get_timestamp(log, stream)
    rosmsg = Mock([])
    bagmsg = Mock([], timestamp=42)
    nanosec = get_timestamp(rosmsg, bagmsg)
    assert nanosec == 42

    # ROS2 below magic
    log = Mock([])
    stream = Mock([], rosbag2=True)
    get_timestamp = make_get_timestamp(log, stream)
    rosmsg = Mock([], header=Mock(stamp=Mock([], sec=0, nanosec=0)))
    bagmsg = Mock([], timestamp=42)
    nanosec = get_timestamp(rosmsg, bagmsg)
    assert nanosec == 0

    # ROS2 above magic
    log = Mock(['warning'])
    stream = Mock([], rosbag2=True)
    get_timestamp = make_get_timestamp(log, stream)
    rosmsg = Mock([], header=Mock(stamp=Mock([], sec=0, nanosec=0)))
    bagmsg = Mock([], timestamp=601 * 10**9)
    nanosec = get_timestamp(rosmsg, bagmsg)
    assert nanosec == 601 * 10**9
    log.warning.assert_called_once()

    # ROS2 no fallback
    log = Mock([])
    stream = Mock([], rosbag2=True)
    get_timestamp = make_get_timestamp(log, stream)
    rosmsg = Mock([], header=Mock(stamp=Mock([], sec=2, nanosec=42)))
    bagmsg = Mock([])
    nanosec = get_timestamp(rosmsg, bagmsg)
    assert nanosec == 2 * 10**9 + 42

    # decision remains after first message
    rosmsg = Mock([], header=Mock(stamp=Mock([], sec=0, nanosec=0)))
    bagmsg = Mock([], timestamp=601 * 10**9)
    nanosec = get_timestamp(rosmsg, bagmsg)
    assert nanosec == 0

    # ROS1 no fallback
    log = Mock([])
    stream = Mock([], rosbag2=False)
    get_timestamp = make_get_timestamp(log, stream)
    rosmsg = Mock([], header=Mock(stamp=Mock([], secs=2, nsecs=42)))
    bagmsg = Mock([])
    nanosec = get_timestamp(rosmsg, bagmsg)
    assert nanosec == 2 * 10**9 + 42
