# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import json
from pathlib import Path

import marv_api as marv
import marv_nodes
from marv_api.types import Section, Widget
from marv_detail import make_map_dict

from .bag import bagmeta
from .cam import ffmpeg, images
from .gnss import gnss_plots
from .trajectory import trajectory

# pylint: disable=redefined-outer-name


@marv.node(Widget)
@marv.input('dataset', default=marv_nodes.dataset)
@marv.input('bagmeta', default=bagmeta)
def summary_keyval(dataset, bagmeta):
    """Keyval widget summarizing bag metadata.

    Useful for detail_summary_widgets.
    """
    dataset, bagmeta = yield marv.pull_all(dataset, bagmeta)
    yield marv.push({'keyval': {
        'items': [
            {'title': 'size', 'formatter': 'filesize', 'list': False,
             'cell': {'uint64': sum(x.size for x in dataset.files)}},
            {'title': 'files', 'list': False,
             'cell': {'uint64': len(dataset.files)}},
            {'title': 'start time', 'formatter': 'datetime', 'list': False,
             'cell': {'timestamp': bagmeta.start_time}},
            {'title': 'end time', 'formatter': 'datetime', 'list': False,
             'cell': {'timestamp': bagmeta.end_time}},
            {'title': 'duration', 'formatter': 'timedelta', 'list': False,
             'cell': {'timedelta': bagmeta.duration}},
        ],
    }})


@marv.node(Widget)
@marv.input('dataset', default=marv_nodes.dataset)
@marv.input('bagmeta', default=bagmeta)
def bagmeta_table(bagmeta, dataset):
    """Table widget listing metadata for each bag of dataset.

    Useful for detail_summary_widgets.
    """
    dataset, bagmeta = yield marv.pull_all(dataset, bagmeta)
    columns = [
        {'title': 'Name', 'formatter': 'rellink', 'sortkey': 'title'},
        {'title': 'Size', 'formatter': 'filesize'},
        {'title': 'Start time', 'formatter': 'datetime'},
        {'title': 'End time', 'formatter': 'datetime'},
        {'title': 'Duration', 'formatter': 'timedelta'},
        {'title': 'Message count', 'align': 'right'},
    ]
    rows = []
    bags = list(bagmeta.bags)
    files = list(dataset.files)
    first = Path(files[0].path)
    rb2path = first.parent if first.name == 'metadata.yaml' else None
    for idx, file in enumerate(files):
        path = Path(file.path)
        if rb2path and path.relative_to(rb2path).parts[0] == 'messages':
            continue
        if path.suffix == '.bag':
            bag = bags.pop(0)
            rows.append({'id': idx, 'cells': [
                {'link': {'href': f'{idx}', 'title': path.name}},
                {'uint64': file.size},
                {'timestamp': bag.start_time},
                {'timestamp': bag.end_time},
                {'timedelta': bag.duration},
                {'uint64': bag.msg_count},
            ]})
        else:
            rows.append({'id': idx, 'cells': [
                {'link': {'href': f'{idx}', 'title': path.name}},
                {'uint64': file.size},
                {'void': None},
                {'void': None},
                {'void': None},
                {'void': None},
            ]})
    yield marv.push({'table': {'columns': columns, 'rows': rows}})


@marv.node(Section)
@marv.input('title', default='Position and Orientation')
@marv.input('plots', default=gnss_plots)
def gnss_section(plots, title):
    """Section displaying GNSS plots."""
    # tmps = []
    # tmp = yield marv.pull(plots)
    # while tmp:
    #     tmps.append(tmp)
    #     tmp = yield marv.pull(plots)
    # plots = tmps
    # TODO: no foreaching right now
    plots = [plots]

    widgets = []
    for plot in plots:
        plotfile = yield marv.pull(plot)
        if plotfile:
            widgets.append({'title': plot.title,
                            'image': {'src': plotfile.relpath}})
    assert len({x['title'] for x in widgets}) == len(widgets)
    if widgets:
        yield marv.push({'title': title, 'widgets': widgets})


@marv.node(Widget)
@marv.input('stream', foreach=images)  # images is a stream of streams of images
def galleries(stream):
    """Galleries for all images streams.

    Used by marv_robotics.detail.images_section.
    """
    yield marv.set_header(title=stream.title)
    images = []
    while True:
        img = yield marv.pull(stream)
        if img is None:
            break
        images.append({'src': img.relpath})
    yield marv.push({'title': stream.title, 'gallery': {'images': images}})


@marv.node(Section)
@marv.input('title', default='Images')
@marv.input('galleries', default=galleries)
def images_section(galleries, title):
    """Section with galleries of images for each images stream."""
    tmp = []
    while True:
        msg = yield marv.pull(galleries)
        if msg is None:
            break
        tmp.append(msg)
    galleries = tmp
    galleries = sorted(galleries, key=lambda x: x.title)
    widgets = yield marv.pull_all(*galleries)
    if widgets:
        yield marv.push({'title': title, 'widgets': widgets})


@marv.node(Section)
@marv.input('title', default='Connections')
@marv.input('bagmeta', default=bagmeta)
@marv.input('dataset', default=marv_nodes.dataset)
def connections_section(bagmeta, dataset, title):
    """Section displaying information about ROS connections."""
    dataset, bagmeta = yield marv.pull_all(dataset, bagmeta)
    if not bagmeta.topics:
        raise marv.Abort()
    columns = [
        {'title': 'Topic'},
        {'title': 'Type'},
        {'title': 'MD5'},
        {'title': 'Latching'},
        {'title': 'Message count', 'align': 'right'},
    ]
    rows = [{'id': idx, 'cells': [
        {'text': con.topic},
        {'text': con.datatype},
        {'text': con.md5sum},
        {'bool': con.latching},
        {'uint64': con.msg_count},
    ]} for idx, con in enumerate(bagmeta.connections)]
    widgets = [{'table': {'columns': columns, 'rows': rows}}]
    # TODO: Add text widget explaining what can be seen here: ROS bag
    # files store connections. There can be multiple connections for
    # one topic with the same or different message types and message
    # types with the same name might have different md5s. For
    # simplicity connections with the same topic, message type and md5
    # are treated as one, within one bag file as well as across bags
    # of one set. If one of such connections is latching, the
    # aggregated connection will be latching.
    yield marv.push({'title': title, 'widgets': widgets})


@marv.node(Section)
@marv.input('title', default='Trajectory')
@marv.input('geojson', default=trajectory)
@marv.input('minzoom', default=-30)
@marv.input('maxzoom', default=40)
@marv.input('tile_server_protocol', default='')
def trajectory_section(geojson, title, minzoom, maxzoom, tile_server_protocol):
    """Section displaying trajectory on a map.

    Args:
        title (str): Detail section title.
        geojson: Stream with one GeoJson message.
        minzoom (int): Minimum zoom level.
        maxzoom (int): Maximum zoom level.
        tile_server_protocol (str): Set to ``https:`` if you host marv
            behind http and prefer the tile requests to be secured.

    """
    geojson = yield marv.pull(geojson)
    if not geojson:
        raise marv.Abort()
    layers = [
        {'title': 'Background',
         'tiles': [
             {'title': 'Roadmap',
              'url': (
                  '%s//[abc].osm.ternaris.com/styles/osm-bright/rendered/{z}/{x}/{y}.png'
                  % tile_server_protocol
              ),
              'attribution': (
                  '© <a href="http://openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              ),
              'retina': 3,
              'zoom': {'min': 0, 'max': 20}},
             {'title': 'Satellite',
              'url': (
                  '%s//server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}.png'  # pylint: disable=line-too-long
                  % tile_server_protocol
              ),
              'attribution': (
                  'Sources: Esri, DigitalGlobe, GeoEye, Earthstar Geographics, CNES/Airbus DS, '
                  'USDA, USGS, AeroGRID, IGN, and the GIS User Community'
              ),
              'zoom': {'min': 0, 'max': 18}},
         ]},
        {'title': 'Trajectory',
         'color': (0., 1., 0., 1.),
         'geojson': geojson},
    ]
    dct = make_map_dict({
        'layers': layers,
        'zoom': {'min': minzoom, 'max': maxzoom},
    })
    jsonfile = yield marv.make_file('data.json')
    with open(jsonfile.path, 'w') as f:
        json.dump(dct, f, sort_keys=True)
    yield marv.push({'title': title,
                     'widgets': [{'map_partial': f'marv-partial:{jsonfile.relpath}'}]})


@marv.node(Section)
@marv.input('title', default='Videos')
@marv.input('videos', default=ffmpeg)
def video_section(videos, title):
    """Section displaying one video player per image stream."""
    tmps = []
    while True:
        tmp = yield marv.pull(videos)
        if tmp is None:
            break
        tmps.append(tmp)
    videos = sorted(tmps, key=lambda x: x.title)
    if not videos:
        raise marv.Abort()

    videofiles = yield marv.pull_all(*videos)
    widgets = [
        {
            'title': video.title,
            'video': {'src': videofile.relpath},
        }
        for video, videofile in zip(videos, videofiles)
        if videofile is not None
    ]
    assert len({x['title'] for x in widgets}) == len(widgets)
    if widgets:
        yield marv.push({'title': title, 'widgets': widgets})
