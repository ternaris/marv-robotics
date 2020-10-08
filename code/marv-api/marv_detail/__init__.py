# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import json

import capnp  # pylint: disable=unused-import

from marv_api.utils import err
from marv_pycapnp import Wrapper

from .types_capnp import Detail, Widget  # pylint: disable=import-error,unused-import

FORMATTER_MAP = {
    'acceleration': lambda x: x,
    'date': lambda ns: None if ns is None else int(ns / 10**6),
    'datetime': lambda ns: None if ns is None else int(ns / 10**6),
    'distance': lambda x: x,
    'filesize': lambda x: None if x is None else int(x),
    'float': float,
    'icon[]': lambda x: x,
    'int': int,
    'link': lambda x: x,
    'pill[]': lambda x: x,
    'rellink': lambda x: x,
    'route': lambda x: x,
    'speed': lambda x: x,
    'string': lambda x: x,
    'timedelta': lambda ns: None if ns is None else int(ns / 10**6),
}


def detail_to_dict(obj):
    dct = obj.to_dict(verbose=True, which=True)
    widgets = dct.get('summary', {'widgets': []})['widgets'][:]
    widgets.extend(widget for sec in dct['sections'] for widget in sec['widgets'])
    for widget in widgets:
        try:
            fixup_widget(widget)
        except Exception:
            from pprint import pformat  # pylint: disable=import-outside-toplevel
            err(pformat(dct))
            err(pformat(widget))
            raise
    return dct


def make_map_dict(dct):
    reader = Wrapper.from_dict(Widget.Map, dct)._reader  # pylint: disable=protected-access
    mapdct = reader.to_dict(verbose=True, which=True)
    fixup_map(mapdct)
    return mapdct


def fixup_widget(dct):  # noqa: C901
    # pylint: disable=too-many-branches

    which = dct['type'] = dct.pop('_which')
    data = dct['data'] = dct.pop(which)
    if which == 'custom':
        dct['type'] = data['type']
        dct['data'] = json.loads(data['data'])
    elif which == 'keyval':
        for item in data['items']:
            cell = item.pop('cell')
            transform = FORMATTER_MAP[item['formatter'] + ('[]' if item['list'] else '')]
            item['value'] = transform(cell[cell['_which']])
    elif which == 'link':
        if not data['download']:
            del data['download']
    elif which == 'map':
        fixup_map(data)
    elif which == 'mapPartial':
        dct['type'] = 'map'
        assert data.startswith('marv-partial:'), data
    elif which == 'mpld3' and not data.startswith('marv-partial:'):
        dct['data'] = json.loads(data)
    elif which == 'pointcloud':
        transform = data['transform']
        assert len(transform) == 16, transform
    elif which == 'table':
        formatter = [FORMATTER_MAP[col['formatter'] + ('[]' if col['list'] else '')]
                     for col in data['columns']]
        for row in data['rows']:
            row['values'] = values = []
            for idx, cell in enumerate(row['cells']):
                values.append(formatter[idx](cell[cell['_which']]))
            del row['cells']
        for action in data['actions']:
            action['data'] = json.loads(action['data'])

    if hasattr(data, 'get'):
        for widget in data.get('widgets', []):
            fixup_widget(widget)


def fixup_map(data):
    zoom = data['zoom']
    data['zoom'] = [zoom['min'], zoom['max']]
    for layer in data['layers']:
        transform = layer['transform']
        assert len(transform) == 16, transform
        layer['type'] = layertype = layer.pop('_which')
        if layertype == 'tiles':
            for tile in layer['tiles']:
                zoom = tile['zoom']
                tile['zoom'] = [zoom['min'], zoom['max']]
        elif layertype == 'geojson':
            fixup_geojson(layer['geojson'])
        else:
            raise RuntimeError(layertype)


def fixup_geojson(geojson):  # noqa: C901
    geotype = geojson.pop('_which')
    geojson['type'] = geotype[0].upper() + geotype[1:]
    geojson.update(geojson.pop(geotype))
    if geotype == 'feature':
        fixup_geometry(geojson['geometry'])
    elif geotype == 'featureCollection':
        for feature in geojson['features']:
            feature['type'] = 'Feature'
            fixup_geometry(feature['geometry'])
            properties = feature['properties']
            timestamps = properties['timestamps']
            if timestamps:
                properties['timestamps'] = [int(x / 1e6) for x in timestamps]
            else:
                del properties['timestamps']
            if not properties['rotations']:
                del properties['rotations']
    elif geotype == 'geometryCollection':
        for geo in geojson['geometries']:
            fixup_geometry(geo)
    elif geotype == 'polygon':
        fixup_polygon(geojson['coordinates'])
    elif geotype == 'multiPolygon':
        for poly in geojson['coordinates']:
            fixup_polygon(poly)


def fixup_polygon(linear_rings):
    first = linear_rings[0]
    if not ccw(first):
        first.reverse()
    for coords in linear_rings[1:]:
        if ccw(coords):
            coords.reverse()


def fixup_geometry(geometry):
    which = geometry.pop('_which')
    geometry['type'] = which[0].upper() + which[1:]
    geometry.update(geometry.pop(which))
    if which == 'polygon':
        fixup_polygon(geometry['coordinates'])
    elif which == 'multiPolygon':
        for poly in geometry['coordinates']:
            fixup_polygon(poly)


def ccw(points):
    return sum((x2 + x1) / 2 * (y2 - y1) for (x1, y1), (x2, y2) in
               (points[i:i+2] for i in range(len(points) - 1))) > 0
