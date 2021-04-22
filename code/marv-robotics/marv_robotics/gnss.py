# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=invalid-name,redefined-outer-name

from datetime import datetime

import numpy as np
import utm
from matplotlib import cm
from matplotlib import dates as md
from matplotlib import pyplot as plt

import marv_api as marv
from marv_api.types import File

from .bag import make_deserialize, make_get_timestamp, messages


def yaw_angle(frame):
    rot = np.zeros((3, 3))

    # consists of time, x, y, z, w
    q1 = frame.x
    q2 = frame.y
    q3 = frame.z
    q4 = frame.w

    rot[0, 0] = 1 - 2 * q2 * q2 - 2 * q3 * q3
    rot[0, 1] = 2 * (q1 * q2 - q3 * q4)
    rot[0, 2] = 2 * (q1 * q3 + q2 * q4)
    rot[1, 0] = 2 * (q1 * q2 + q3 * q4)
    rot[1, 1] = 1 - 2 * q1 * q1 - 2 * q3 * q3
    rot[1, 2] = 2 * (q2 * q3 - q1 * q4)
    rot[2, 0] = 2 * (q1 * q3 - q2 * q4)
    rot[2, 1] = 2 * (q1 * q4 + q2 * q3)
    rot[2, 2] = 1 - 2 * q1 * q1 - 2 * q2 * q2

    vec = np.dot(rot, [1, 0, 0])
    return np.arctan2(vec[1], vec[0])


@marv.node()
@marv.input('stream', foreach=marv.select(messages, ('*:sensor_msgs/NavSatFix,'
                                                     '*:sensor_msgs/msg/NavSatFix')))
def positions(stream):
    yield marv.set_header(title=stream.topic)
    log = yield marv.get_logger()
    deserialize = make_deserialize(stream)
    get_timestamp = make_get_timestamp(log, stream)

    erroneous = 0
    e_offset = None
    n_offset = None
    u_offset = None
    positions = []
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        rosmsg = deserialize(msg.data)

        if not hasattr(rosmsg, 'status') or \
           np.isnan(rosmsg.longitude) or \
           np.isnan(rosmsg.latitude) or \
           np.isnan(rosmsg.altitude) or \
           np.isnan(rosmsg.position_covariance[0]):
            erroneous += 1
            continue

        e, n, _, _ = utm.from_latlon(rosmsg.latitude, rosmsg.longitude)
        if e_offset is None:
            e_offset = e
            n_offset = n
            u_offset = rosmsg.altitude
        e = e - e_offset
        n = n - n_offset
        u = rosmsg.altitude - u_offset

        positions.append([get_timestamp(rosmsg, msg) / 1e9,
                          rosmsg.latitude,
                          rosmsg.longitude,
                          rosmsg.altitude,
                          e, n, u,
                          rosmsg.status.status,
                          np.sqrt(rosmsg.position_covariance[0])])
    if erroneous:
        log = yield marv.get_logger()
        log.warning('skipped %d erroneous messages', erroneous)
    if positions:
        yield marv.push({'values': positions})


@marv.node()
@marv.input('stream', foreach=marv.select(messages, ('*:sensor_msgs/Imu,'
                                                     '*:sensor_msgs/msg/Imu')))
def imus(stream):
    yield marv.set_header(title=stream.topic)
    log = yield marv.get_logger()
    deserialize = make_deserialize(stream)
    get_timestamp = make_get_timestamp(log, stream)

    erroneous = 0
    imus = []
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        rosmsg = deserialize(msg.data)
        if np.isnan(rosmsg.orientation.x):
            erroneous += 1
            continue

        imus.append([get_timestamp(rosmsg, msg) / 1e9,
                     yaw_angle(rosmsg.orientation)])
    if erroneous:
        log = yield marv.get_logger()
        log.warning('skipped %d erroneous messages', erroneous)
    yield marv.push({'values': imus})


@marv.node()
@marv.input('stream', foreach=marv.select(messages, ','.join([
    '*:nmea_navsat_driver/NavSatOrientation',
    '*:nmea_navsat_driver/msg/NavSatOrientation',
])))
def navsatorients(stream):
    yield marv.set_header(title=stream.topic)
    log = yield marv.get_logger()
    deserialize = make_deserialize(stream)
    get_timestamp = make_get_timestamp(log, stream)

    erroneous = 0
    navsatorients = []
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break

        rosmsg = deserialize(msg.data)
        if np.isnan(rosmsg.yaw):
            erroneous += 1
            continue

        navsatorients.append([get_timestamp(rosmsg, msg) / 1e9,
                              rosmsg.yaw])
    if erroneous:
        log.warning('skipped %d erroneous messages', erroneous)
    yield marv.push({'values': navsatorients})


@marv.node(group=True)
@marv.input('imus', default=imus)
@marv.input('navsatorients', default=navsatorients)
def orientations(imus, navsatorients):
    while True:
        tmp = yield marv.pull(imus)
        if tmp is None:
            break
        yield marv.push(tmp)
    while True:
        tmp = yield marv.pull(navsatorients)
        if tmp is None:
            break
        yield marv.push(tmp)


@marv.node(File)
# @marv.input('gps', foreach=positions)
# @marv.input('orientation', foreach=orientations)
@marv.input('gps', default=positions)
@marv.input('orientation', default=orientations)
def gnss_plots(gps, orientation):
    # pylint: disable=too-many-locals,too-many-statements

    # TODO: framework does not yet support multiple foreach
    # pick only first combination for now

    log = yield marv.get_logger()
    gps, orientation = yield marv.pull_all(gps, orientation)
    if gps is None:
        log.error('No gps messages')
        raise marv.Abort()
    gtitle = gps.title

    gps = yield marv.pull(gps)  # There is only one message

    # Check whether there are any valid messages left
    if gps is None:
        log.error('No valid gps messages')
        raise marv.Abort()

    gps = gps['values']
    if orientation is not None:
        otitle = orientation.title
        orientation = yield marv.pull(orientation)
    if orientation is None:
        log.warning('No orientations found')
        otitle = 'none'
        orientation = []
    else:
        orientation = orientation['values']

    name = '__'.join(x.replace('/', ':')[1:] for x in [gtitle, otitle]) + '.jpg'
    title = f'{gtitle} with {otitle}'
    yield marv.set_header(title=title)
    plotfile = yield marv.make_file(name)

    fig = plt.figure()
    fig.subplots_adjust(wspace=0.3)

    ax1 = fig.add_subplot(1, 3, 1)  # e-n plot
    ax2 = fig.add_subplot(2, 3, 2)  # orientation plot
    ax3 = fig.add_subplot(2, 3, 3)  # e-time plot
    ax4 = fig.add_subplot(2, 3, 5)  # up plot
    ax5 = fig.add_subplot(2, 3, 6)  # n-time plot

    # masking for finite values
    gps = np.array(gps)
    gps = gps[np.isfinite(gps[:, 1])]

    # precompute plot vars
    c = cm.prism(gps[:, 7]/2)  # pylint: disable=no-member

    ax1.scatter(gps[:, 4], gps[:, 5], c=c, edgecolor='none', s=3,
                label='green: RTK\nyellow: DGPS\nred: Single')

    xfmt = md.DateFormatter('%H:%M:%S')
    ax3.xaxis.set_major_formatter(xfmt)
    ax4.xaxis.set_major_formatter(xfmt)
    ax5.xaxis.set_major_formatter(xfmt)

    if orientation:
        ax2.xaxis.set_major_formatter(xfmt)
        orientation = np.array(orientation)
        ax2.plot([datetime.fromtimestamp(x) for x in orientation[:, 0]],  # noqa: DTZ
                 orientation[:, 1])

    ax3.plot([datetime.fromtimestamp(x) for x in gps[:, 0]], gps[:, 4])  # noqa: DTZ
    ax4.plot([datetime.fromtimestamp(x) for x in gps[:, 0]], gps[:, 6])  # noqa: DTZ
    ax5.plot([datetime.fromtimestamp(x) for x in gps[:, 0]], gps[:, 5])  # noqa: DTZ

    fig.autofmt_xdate()

    ax1.legend(loc='upper right', title='')

    ax1.set_ylabel('GNSS northing [m]')
    ax1.set_xlabel('GNSS easting [m]')
    ax2.set_ylabel('Heading over time [rad]')
    ax3.set_ylabel('GNSS easting over time [m]')
    ax4.set_ylabel('GNSS height over time [m]')
    ax5.set_ylabel('GNSS northing over time [m]')

    fig.set_size_inches(16, 9)
    try:
        fig.savefig(plotfile.path)
    finally:
        plt.close()
    yield plotfile
