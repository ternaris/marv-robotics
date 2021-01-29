# Copyright 2019 - 2020  Ternaris, all rights reserved.
# SPDX-License-Identifier: PROPRIETARY

"""Nodes processing motion data."""

# pylint: disable=redefined-outer-name

import json
import math
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

import numpy
import utm

import marv_api as marv
from marv_api.types import Float64Value
from marv_detail.types_capnp import Section  # pylint: disable=no-name-in-module
from marv_robotics.bag import make_deserialize, make_get_timestamp, messages


@marv.node()
@marv.input('stream', marv.select(messages, '*:sensor_msgs/NavSatFix'))
# @marv.input('stream', marv.select(messages, '*:geometry_msgs/PoseStamped'))
def motion_timestamp(stream):
    """Extract timestamps for motion events.

    Args:
        stream: ROS message stream with Pose or GPS messages.

    Yields:
        Message stream with timestamps.

    """
    log = yield marv.get_logger()
    stream = yield marv.pull(stream)  # take first matching connection
    if not stream:
        return

    yield marv.set_header(title=stream.topic)
    deserialize = make_deserialize(stream)
    get_timestamp = make_get_timestamp(log, stream)
    while msg := (yield marv.pull(stream)):
        rosmsg = deserialize(msg.data)
        yield marv.push(get_timestamp(rosmsg, msg))


@marv.node()
@marv.input('stream', marv.select(messages, '*:geometry_msgs/PoseStamped'))
def position_xyz(stream):
    """Extract position from Pose.

    Args:
        stream: ROS message stream with Pose messages.

    Yields:
        Message stream with Cartesian positions.

    """
    stream = yield marv.pull(stream)
    if not stream:
        return

    yield marv.set_header(title=stream.topic)
    deserialize = make_deserialize(stream)
    while msg := (yield marv.pull(stream)):
        rosmsg = deserialize(msg.data)
        pos = rosmsg.pose.position
        yield marv.push({'x': pos.x, 'y': pos.y, 'z': pos.z})


@marv.node()
@marv.input('stream', marv.select(messages, '*:sensor_msgs/NavSatFix'))
def position_gps(stream):
    """Extract position from GPS.

    Args:
        stream: ROS message stream with GPS messages.

    Yields:
        Message stream with GPS positions.

    """
    stream = yield marv.pull(stream)
    if not stream:
        return

    yield marv.set_header(title=stream.topic)
    deserialize = make_deserialize(stream)
    while msg := (yield marv.pull(stream)):
        rosmsg = deserialize(msg.data)
        yield marv.push({'lat': rosmsg.latitude, 'lon': rosmsg.longitude, 'alt': rosmsg.altitude})


@marv.node()
def dummy():
    yield


@marv.node()
@marv.input('timestamp', dummy)
@marv.input('pos', dummy)
@marv.input('pvar', type=float)
@marv.input('qvar', type=float)
@marv.input('rvar', type=float)
@marv.input('keys', (), type=tuple)
def filter_pos(timestamp, pos, pvar, qvar, rvar, keys):  # pylint: disable=too-many-arguments,too-many-locals
    """Kalman filter input stream using simple linear motion model.

    Args:
        timestamp: Message stream with timestamps corresponding to pos.
        pos: Message stream with positional data.
        pvar: Model uncertainty.
        qvar: Process uncertainty.
        rvar: Measurement uncertainty.
        keys: Keynames of positional data.

    Yields:
        Message stream with filtered positions.

    """
    # pylint: disable=invalid-name
    msg_ts, msg_pos = yield marv.pull_all(timestamp, pos)
    if msg_ts is None or msg_pos is None:
        return

    yield marv.set_header(title=timestamp.title)
    yield marv.push(msg_pos)

    F = numpy.eye(6)
    x = numpy.array([
        msg_pos[keys[0]], 0.,
        msg_pos[keys[1]], 0.,
        msg_pos[keys[2]], 0.,
    ])
    P = numpy.eye(6) * pvar
    Q = numpy.eye(6)

    R = numpy.eye(3) * rvar
    H = numpy.array([
        [1, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 1, 0],
    ])

    last_ts = msg_ts
    while True:
        msg_ts, msg_pos = yield marv.pull_all(timestamp, pos)
        if msg_ts is None or msg_pos is None:
            return

        dt = (msg_ts - last_ts) / 1e9
        last_ts = msg_ts

        F[0, 1] = dt
        F[2, 3] = dt
        F[4, 5] = dt

        G = numpy.array([[.5 * dt**2, dt]]).T
        subQ = G.dot(G.T) * qvar
        Q[0:2, 0:2] = subQ
        Q[2:4, 2:4] = subQ
        Q[4:6, 4:6] = subQ

        x = F.dot(x)
        P = F.dot(P).dot(F.T) + Q

        z = numpy.array([msg_pos[x] for x in keys])
        K = P.dot(H.T).dot(numpy.linalg.inv(H.dot(P).dot(H.T) + R))
        x = x + K.dot(z - H.dot(x))
        P = P - K.dot(H).dot(P)

        res = H.dot(x)
        yield marv.push({x: float(res[i]) for i, x in enumerate(keys)})


@marv.node(Float64Value)
@marv.input('pos', filter_pos.clone(timestamp=motion_timestamp, pos=position_xyz,
                                    pvar=100., qvar=4., rvar=.1, keys=['x', 'y', 'z']))
# @marv.input('pos', position_xyz)  # use this input for unfiltered data
def distance_xyz(pos):
    """Calculate distance from Cartesian positions.

    Args:
        pos: Message stream with Cartesian position messages.

    Yields:
        Message stream with distances.

    """
    msg = yield marv.pull(pos)
    if msg is None:
        return

    yield marv.set_header(title=pos.title)
    yield marv.push({'value': 0})
    prev = msg

    while msg := (yield marv.pull(pos)):
        diffe = msg['x'] - prev['x']
        diffn = msg['y'] - prev['y']
        diffa = msg['z'] - prev['z']
        dist = (diffe**2 + diffn**2 + diffa**2)**0.5
        yield marv.push({'value': dist})
        prev = msg


@marv.node(Float64Value)
@marv.input('pos', filter_pos.clone(timestamp=motion_timestamp, pos=position_gps,
                                    pvar=100., qvar=1e-17, rvar=1e-18,
                                    keys=['lat', 'lon', 'alt']))
# @marv.input('pos', position_gps)  # use this input for unfiltered data
def distance_gps(pos):
    """Calculate distance from GPS positions.

    Args:
        pos: Message stream with GPS position messages.

    Yields:
        Message stream with distances.

    """
    msg = yield marv.pull(pos)
    if msg is None:
        return

    yield marv.set_header(title=pos.title)
    yield marv.push({'value': 0})
    lat_p = radians(msg['lat'])
    lon_p = radians(msg['lon'])
    alt_p = msg['alt']

    while msg := (yield marv.pull(pos)):
        lat = radians(msg['lat'])
        lon = radians(msg['lon'])
        alt = msg['alt']
        lat_d = lat_p - lat
        lon_d = lon_p - lon
        alt_d = alt_p - alt
        dis = sin(lat_d * 0.5) ** 2 + cos(lat) * cos(lat_p) * sin(lon_d * 0.5) ** 2
        dis = 2 * 6371008.8 * asin(sqrt(dis))
        if not math.isnan(alt_d):
            dis = sqrt(dis**2 + alt_d**2)  # euclidean approx taking altitude into account
        yield marv.push({'value': dis})
        lat_p = lat
        lon_p = lon
        alt_p = alt


@marv.node(Float64Value)
@marv.input('timestamp', motion_timestamp)
@marv.input('distance', distance_gps)
def speed(timestamp, distance):
    """Calculate speed from distance stream.

    This node calculates the speed values from distance values. It is useful in cases where no speed
    data from a sensor is available.

    Args:
        timestamp: Message stream with timestamps of distances.
        distance: Message stream with distance values.

    Yields:
        Message stream with speed values.

    """
    msg_ts, msg_dist = yield marv.pull_all(timestamp, distance)
    if msg_ts is None or msg_dist is None:
        return

    yield marv.set_header(title=timestamp.title)
    yield marv.push({'value': 0})
    pts = msg_ts

    while (msg_ts := (yield marv.pull(timestamp))) and (msg_dist := (yield marv.pull(distance))):
        speed = msg_dist.value * 1e9 / (msg_ts - pts)
        yield marv.push({'value': speed})
        pts = msg_ts


@marv.node(Float64Value)
@marv.input('timestamp', motion_timestamp)
@marv.input('speed', speed)
def acceleration(timestamp, speed):
    """Calculate acceleration from speed stream.

    This node calculates the acceleration values from speed values. It is useful in cases where no
    acceleration data from a sensor is available.

    Args:
        timestamp: Message stream with timestamps of distances.
        speed: Message stream with speed values.

    Yields:
        Message stream with acceleration values.

    """
    msg_ts, msg_speed = yield marv.pull_all(timestamp, speed)
    if msg_ts is None or msg_speed is None:
        return

    msg_ts, msg_speed = yield marv.pull_all(timestamp, speed)
    if msg_ts is None or msg_speed is None:
        return

    yield marv.set_header(title=timestamp.title)
    yield marv.push({'value': 0})
    yield marv.push({'value': 0})
    pts = msg_ts
    psp = msg_speed.value

    while (msg_ts := (yield marv.pull(timestamp))) and (msg_speed := (yield marv.pull(speed))):
        acceleration = (msg_speed.value - psp) * 1e9 / (msg_ts - pts)
        yield marv.push({'value': acceleration})
        pts = msg_ts
        psp = msg_speed.value


def empty_trace(name, tracetype):
    """Create empty trace.

    Args:
        name: Name of the trace.
        tracetype: Type of plot

    Returns:
        Trace data.

    """
    return {
        'x': [],
        'y': [],
        'type': tracetype,
        'name': name,
        'mode': 'lines',
    }


def empty_plotly_widget(trace, title):
    """Create empty plotly widget.

    Args:
        trace: Trace data.
        title: Y-axis title.

    Returns:
        Ploty widget data.

    """
    return {
        'data': [trace],
        'layout': {
            'hovermode': False,
            'height': 290,
            'margin': {
                't': 0,
                'b': 40,
            },
            'xaxis': {
                'type': 'date',
            },
            'yaxis': {
                'title': title,
            },
        },
        'config': {
            'displayModeBar': False,
            'doubleClickDelay': 600,
        },
    }


@marv.node()
@marv.input('stream', marv.select(messages, '*:sensor_msgs/NavSatFix'))
# @marv.input('stream', marv.select(messages, '*:geometry_msgs/PoseStamped'))
def easting_northing(stream):
    """Extract easting and northing.

    Args:
        stream: ROS message stream with Pose or GPS messages.

    Yields:
        Message stream with easting and northing.

    """
    stream = yield marv.pull(stream)  # take first matching connection
    if not stream:
        return

    yield marv.set_header(title=stream.topic)
    deserialize = make_deserialize(stream)
    while msg := (yield marv.pull(stream)):
        rosmsg = deserialize(msg.data)
        if stream.msg_type == 'sensor_msgs/NavSatFix':
            easting, northing, _, _ = utm.from_latlon(rosmsg.latitude, rosmsg.longitude)
        else:
            easting, northing = rosmsg.pose.position.x, rosmsg.pose.position.y
        yield marv.push({'e': easting, 'n': northing})


@marv.node(Section)
@marv.input('timestamp', motion_timestamp)
@marv.input('easting_northing', easting_northing)
@marv.input('distance', distance_gps)
@marv.input('speed', speed)
@marv.input('acceleration', acceleration)
def motion_section(timestamp, easting_northing, distance, speed, acceleration):  # pylint: disable=too-many-arguments,too-many-locals
    """Create motion section.

    Args:
        timestamp: Message stream of timestamps.
        easting_northing: Message stream of easting/northing coordinates.
        distance: Message stream of distances.
        speed: Message stream of speeds.
        acceleration: Message stream of accelerations.

    Yields:
        Motion section for frontend.

    """
    yield marv.set_header()

    traces = {
        name: empty_trace(name, 'scatter')
        for name in ['en', 'distance', 'speed', 'acceleration']
    }
    plots = {
        name: empty_plotly_widget(trace, name)
        for name, trace in traces.items()
    }
    # customize individual plots
    del plots['en']['layout']['xaxis']['type']
    plots['en']['layout']['xaxis']['title'] = 'filtered easting (m)'
    plots['en']['layout']['yaxis']['title'] = 'filtered northing (m)'
    plots['en']['layout']['yaxis']['scaleanchor'] = 'x'
    plots['en']['layout']['yaxis']['scaleratio'] = 1
    plots['distance']['layout']['yaxis']['title'] = 'distance driven (m)'
    plots['speed']['layout']['yaxis']['title'] = 'speed (m/s)'
    del plots['acceleration']['layout']['margin']
    plots['acceleration']['layout']['yaxis']['title'] = 'acceleration (m/s²)'

    firste = None
    firstn = None
    distsum = 0
    while True:
        msg_ts, msg_en, msg_distance, msg_speed, msg_acceleration = yield marv.pull_all(
            timestamp, easting_northing, distance, speed, acceleration)
        if msg_ts is None or msg_en is None or msg_distance is None or msg_speed is None or \
                msg_acceleration is None:
            break

        if firste is None:
            firste = msg_en['e']
            firstn = msg_en['n']
            rele = 0
            reln = 0
        else:
            rele = msg_en['e'] - firste
            reln = msg_en['n'] - firstn

        traces['en']['x'].append(rele)
        traces['en']['y'].append(reln)

        tsval = int(msg_ts / 1e6)
        traces['distance']['x'].append(tsval)
        traces['speed']['x'].append(tsval)
        traces['acceleration']['x'].append(tsval)

        distsum += msg_distance.value
        traces['distance']['y'].append(distsum)
        traces['speed']['y'].append(msg_speed.value)
        traces['acceleration']['y'].append(msg_acceleration.value)

    if traces['distance']['x']:
        file_en = yield marv.make_file('easting_northing.json')
        Path(file_en.path).write_text(json.dumps(plots['en']))
        file_dist = yield marv.make_file('distance.json')
        Path(file_dist.path).write_text(json.dumps(plots['distance']))
        file_speed = yield marv.make_file('speed.json')
        Path(file_speed.path).write_text(json.dumps(plots['speed']))
        file_accel = yield marv.make_file('acceleration.json')
        Path(file_accel.path).write_text(json.dumps(plots['acceleration']))
        yield marv.push({'title': 'Motion plots', 'widgets': [
            {'title': '', 'plotly': f'marv-partial:{file_en.relpath}'},
            {'title': '', 'plotly': f'marv-partial:{file_dist.relpath}'},
            {'title': '', 'plotly': f'marv-partial:{file_speed.relpath}'},
            {'title': '', 'plotly': f'marv-partial:{file_accel.relpath}'},
        ]})
