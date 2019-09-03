# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import json
import mimetypes
import pathlib

from aiohttp import web

from marv_node.setid import SetID
from .tooling import api_group as marv_api_group


@marv_api_group()
def dataset(_):
    pass


@dataset.endpoint('/file-list', methods=['POST'])
async def file_list(request):
    ids = await request.json()
    if not ids:
        raise web.HTTPBadRequest()

    # TODO: remove scanroot prefix?

    datasets = await request.app['site'].db.get_datasets_by_dbids(ids, prefetch=('files',))

    paths = sorted(x.path for dataset in datasets for x in dataset.files)
    urls = [f'dataset/{dataset.setid}/{x.idx}' for dataset in datasets for x in dataset.files]

    # TODO: complain about invalid/unknown ids?

    return web.json_response({'paths': paths, 'urls': urls})


async def _send_detail_json(request, setid, setdir):
    try:
        with (setdir / 'detail.json').open() as f:
            detail = json.load(f)  # pylint: disable=redefined-outer-name
    except IOError:
        raise web.HTTPNotFound()

    site = request.app['site']
    query = await site.db.get_datasets_by_setids((setid,), prefetch=('comments', 'tags'))
    dataset = query[0]  # pylint: disable=redefined-outer-name
    detail.update({
        'collection': dataset.collection,
        'id': dataset.id,
        'setid': str(dataset.setid),
        'comments': [{'author': x.author, 'text': x.text, 'timeAdded': x.time_added}
                     for x in sorted(dataset.comments, key=lambda x: x.time_added)],
        'tags': [x.value for x in sorted(dataset.tags, key=lambda x: x.value)],
        'all_known_tags': await site.db.get_all_known_tags_for_collection(dataset.collection),
    })

    resp = web.json_response(detail, headers={'Cache-Control': 'no-cache'})
    return resp


@dataset.endpoint('/dataset/{setid:[^/]+}{_:/?}{path:((?<=/).*)?}')
async def detail(request):
    setid = request.match_info['setid']
    path = request.match_info['path'] or 'detail.json'
    try:
        setid = str(SetID(setid))
    except TypeError:
        raise web.HTTPNotFound()

    setdir = pathlib.Path(request.app['site'].config.marv.storedir) / setid

    if path == 'detail.json':
        return await _send_detail_json(request, setid, setdir)

    if path.isdigit():
        pathstr = await request.app['site'].db.get_filepath_by_setid_idx(setid, int(path))
        path = pathlib.Path(pathstr)
    else:
        path = setdir / path
        if '..' in path.parts:
            raise web.HTTPBadRequest()

    # Make sure path exists and is safe
    if not path.is_absolute() \
       or not path.is_file():
        raise web.HTTPNotFound()

    if request.app['site'].config.marv.reverse_proxy == 'nginx':
        mime = mimetypes.guess_type(str(path))
        approot = request.path.split('/marv/api/dataset/')[0]
        return web.Response(headers={
            'content-type': mime[0] if mime[0] else 'application/octet-stream',
            'cache-control': 'no-cache',
            'x-accel-buffering': 'no',
            'x-accel-redirect': f'{approot}{str(path)}',
            'Content-Disposition': f'attachment; filename={path.name}',
        })

    try:
        return web.FileResponse(path, headers={
            'Cache-Control': 'no-cache',
            'Content-Disposition': f'attachment; filename={path.name}',
        })
    except ValueError:
        raise web.HTTPNotFound()
