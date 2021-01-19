# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import numpy as np

import marv_api as marv
from marv_api.types import GeoJson

from .bag import make_deserialize, make_get_timestamp, messages


@marv.node()
@marv.input('stream', foreach=marv.select(messages, ('*:sensor_msgs/NavSatFix,'
                                                     '*:sensor_msgs/msg/NavSatFix')))
def navsatfix(stream):
    yield marv.set_header(title=stream.topic)
    log = yield marv.get_logger()
    deserialize = make_deserialize(stream)
    get_timestamp = make_get_timestamp(log, stream)
    erroneous = 0
    while True:
        msg = yield marv.pull(stream)
        if msg is None:
            break
        rosmsg = deserialize(msg.data)

        if not hasattr(rosmsg, 'status') or \
           np.isnan(rosmsg.longitude) or \
           np.isnan(rosmsg.latitude) or \
           np.isnan(rosmsg.altitude):
            erroneous += 1
            continue

        yield marv.push({
            'status': rosmsg.status.status,
            'lon': rosmsg.longitude,
            'lat': rosmsg.latitude,
            'timestamp': get_timestamp(rosmsg, msg),
        })

    if erroneous:
        log.warning('skipped %d erroneous messages', erroneous)


def _create_feature(coords, quality, timestamps):
    if len(coords) == 1:
        coords = coords[0]
        geotype = 'point'
    else:
        geotype = 'line_string'

    color = ((1., 0.00, 0., 1.),  # rgba
             (1., 0.65, 0., 1.),
             (0., 0.00, 1., 1.),
             (0., 1.00, 0., 1.))[quality]
    return {
        'properties': {
            'color': color,
            'width': 4.,
            'timestamps': timestamps,
            'markervertices': [c * 30 for c in (0., 0., -1., .3, -1., -.3)]},
        'geometry': {geotype: {'coordinates': coords}},
    }


@marv.node(GeoJson)
@marv.input('navsatfixes', default=navsatfix)
def trajectory(navsatfixes):
    # Only one topic for now
    navsatfix = yield marv.pull(navsatfixes)  # pylint: disable=redefined-outer-name
    if not navsatfix:
        raise marv.Abort()
    yield marv.set_header(title=navsatfix.title)
    features = []
    quality = None
    coords = []
    timestamps = []
    while True:
        msg = yield marv.pull(navsatfix)
        if msg is None:
            break

        timestamps.append(msg['timestamp'])

        # Whether to output an augmented fix is determined by both the fix
        # type and the last time differential corrections were received.  A
        # fix is valid when status >= STATUS_FIX.
        # STATUS_NO_FIX =  -1 -> unable to fix position       -> color id 0 = red
        # STATUS_FIX =      0 -> unaugmented fix              -> color id 1 = orange
        # STATUS_SBAS_FIX = 1 -> satellite-based augmentation -> color id 2 = blue
        # STATUS_GBAS_FIX = 2 -> ground-based augmentation    -> color id 3 = green
        #                     -> unknown status id            -> color id 4 = black
        if -1 <= msg['status'] <= 2:
            new_quality = msg['status'] + 1
        else:
            new_quality = 4

        # start new feature if quality changed
        if quality != new_quality:
            if coords:
                features.append(_create_feature(coords, quality, timestamps))
            quality = new_quality
            coords = []
            timestamps = []

        coords.append((msg['lon'], msg['lat']))

    if coords:
        features.append(_create_feature(coords, quality, timestamps))

    if features:
        out = {'feature_collection': {'features': features}}
        yield marv.push(out)
