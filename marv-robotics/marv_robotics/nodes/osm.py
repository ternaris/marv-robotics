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

import marv
import numpy as np


@marv.node()
@marv.input('messages', filter=['*:sensor_msgs/NavSatFix'])
def navsatfix(messages):
    coords = defaultdict(list)
    erroneous = defaultdict(int)
    for topic, msg, _ in messages:
        # skip erroneous messages
        if not hasattr(msg, 'status') or \
           np.isnan(msg.longitude) or \
           np.isnan(msg.latitude) or \
           np.isnan(msg.altitude):
            erroneous[topic] += 1
        else:
            coords[topic].append((msg.status.status, (msg.longitude, msg.latitude)))

    if erroneous:
        marv.log_warn('Skipped erroneous GNSS messages %r', erroneous.items())

    return {'coordinates': coords} if coords else None


@marv.node()
@marv.input('navsatfix')
def geo_json_trajectory(navsatfix):
    features = []
    prev_quality = None
    coordinates = navsatfix.coordinates.values()[0]  # Only one topic for now
    for status, coord in coordinates:
        # Whether to output an augmented fix is determined by both the fix
        # type and the last time differential corrections were received.  A
        # fix is valid when status >= STATUS_FIX.
        # STATUS_NO_FIX =  -1 -> unable to fix position       -> color id 0 = red
        # STATUS_FIX =      0 -> unaugmented fix              -> color id 1 = orange
        # STATUS_SBAS_FIX = 1 -> satellite-based augmentation -> color id 2 = blue
        # STATUS_GBAS_FIX = 2 -> ground-based augmentation    -> color id 3 = green
        #                     -> unknown status id            -> color id 4 = black
        if -1 <= status <= 2:
            quality = status + 1
        else:
            quality = 4
        if quality != prev_quality:
            color = ('#f00', '#ffa500', '#00f', '#0f0', '#000')[quality]
            coords = []
            feat = {'type': 'Feature',
                    'properties': {'style': {'color': color}},
                    'geometry': {'type': 'LineString', 'coordinates': coords}}
            features.append(feat)
            prev_quality = quality
        coords.append(coord)
    return {'type': 'FeatureCollection', 'features': features} if features else None
