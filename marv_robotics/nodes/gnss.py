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

from collections import defaultdict
from datetime import datetime
from itertools import product

import marv
import matplotlib; matplotlib.use('Agg')
import numpy as np
import utm
from matplotlib import cm
from matplotlib import dates as md
from matplotlib import pyplot as plt


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

    # calculate the angle
    return np.arctan2(vec[1], vec[0])


def render(name, gps, orientation):
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
    c = cm.prism(gps[:, 7]/2)

    ax1.scatter(gps[:, 4], gps[:, 5], c=c, edgecolor='none', s=3,
                label="green: RTK\nyellow: DGPS\nred: Single")

    xfmt = md.DateFormatter('%H:%M:%S')
    ax2.xaxis.set_major_formatter(xfmt)
    ax3.xaxis.set_major_formatter(xfmt)
    ax4.xaxis.set_major_formatter(xfmt)
    ax5.xaxis.set_major_formatter(xfmt)

    if orientation:
        orientation = np.array(orientation)
        ax2.plot([datetime.fromtimestamp(x) for x in orientation[:, 0]],
                 orientation[:, 1])

    ax3.plot([datetime.fromtimestamp(x) for x in gps[:, 0]], gps[:, 4])
    ax4.plot([datetime.fromtimestamp(x) for x in gps[:, 0]], gps[:, 6])
    ax5.plot([datetime.fromtimestamp(x) for x in gps[:, 0]], gps[:, 5])

    fig.autofmt_xdate()

    # add the legends
    ax1.legend(loc="best")

    ax1.set_ylabel('GNSS northing [m]')
    ax1.set_xlabel('GNSS easting [m]')
    ax2.set_ylabel('Heading over time [rad]')
    ax3.set_ylabel('GNSS easting over time [m]')
    ax4.set_ylabel('GNSS height over time [m]')
    ax5.set_ylabel('GNSS northing over time [m]')

    fig.set_size_inches(16, 9)
    plt_path, plt_id = marv.make_file(name)

    try:
        fig.savefig(plt_path)
    finally:
        plt.close()

    return plt_id


@marv.node()
@marv.input('messages', filter=['*:sensor_msgs/NavSatFix', '*:sensor_msgs/Imu',
                                '*:nmea_navsat_driver/NavSatOrientation'])
def gnss_plots(messages):
    erroneous = defaultdict(int)
    positions = defaultdict(list)
    e_offset = defaultdict(float)
    n_offset = defaultdict(float)
    u_offset = defaultdict(float)
    orientations = defaultdict(list)
    for topic, msg, _ in messages:
        if msg._type == 'sensor_msgs/NavSatFix':
            # skip erroneous messages
            if not hasattr(msg, 'status') or \
               np.isnan(msg.longitude) or \
               np.isnan(msg.latitude) or \
               np.isnan(msg.altitude):
                erroneous[topic] += 1
                continue

            e, n, _, _ = utm.from_latlon(msg.longitude, msg.latitude)
            e, n, u = (e - e_offset[topic],
                       n - n_offset[topic],
                       msg.altitude - u_offset[topic])
            positions[topic].append([msg.header.stamp.to_sec(),
                                     msg.latitude,
                                     msg.longitude,
                                     msg.altitude,
                                     e, n, u,
                                     msg.status.status,
                                     np.sqrt(msg.position_covariance[0])])

        elif msg._type == 'sensor_msgs/Imu':
            if np.isnan(msg.orientation.x):
                erroneous[topic] += 1
                continue

            orientations[topic].append([msg.header.stamp.to_sec(),
                                        yaw_angle(msg.orientation)])
        elif msg._type == 'nmea_navsat_driver/NavSatOrientation':
            if np.isnan(msg.yaw):
                erroneous[topic] += 1
                continue

            orientations[topic].append([msg.header.stamp.to_sec(),
                                        msg.yaw])
        else:
            raise RuntimeError('Did not ask for {}:{}'.format(topic, msg._type))

    if erroneous:
        marv.log_warn('Skipped erroneous GNSS messages %r', erroneous.items())

    if not positions:
        marv.log_warn('Aborting due to missing positions')
        return None

    if not orientations:
        marv.log_warn('No orientations found')
        orientations['none'] = []

    _plots = {}
    for ptopic, otopic in product(positions, orientations):
        if not positions[ptopic]:
            marv.log_warn('Skipping %s due to missing gps messages', ptopic)
            continue

        key = '{} with {}'.format(ptopic, otopic)
        _plots[key] = render('__'.join([ptopic, otopic]).replace("/", "_") + '.jpg',
                             positions[ptopic], orientations[otopic])
    return _plots
