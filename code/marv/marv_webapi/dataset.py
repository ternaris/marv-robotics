# Copyright 2016 - 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import json
import mimetypes
from pathlib import Path

from aiohttp import web

from marv.db import DBPermissionError
from marv_node.setid import SetID
from .tooling import HTTPPermissionError, api_group as marv_api_group, get_local_granted, safejoin


@marv_api_group()
def dataset(_):
    pass


@dataset.endpoint('/file-list', methods=['POST'], acl_key='download_raw')
async def file_list(request):
    try:
        ids = await request.json()
    except json.JSONDecodeError:
        raise web.HTTPBadRequest

    if not ids:
        raise web.HTTPBadRequest

    try:
        datasets = await request.app['site'].db.get_datasets_by_dbids(
            ids,
            user=request['username'],
            action='download_raw',
            prefetch=('files',),
        )
    except DBPermissionError:
        raise HTTPPermissionError(request)

    paths = sorted(x.path for dataset in datasets for x in dataset.files)
    urls = [f'dataset/{dataset.setid}/{x.idx}' for dataset in datasets for x in dataset.files]

    return web.json_response({'paths': paths, 'urls': urls})


async def _send_detail_json(request, setid, setdir):
    site = request.app['site']
    try:
        query = await site.db.get_datasets_by_setids((setid,), user=request['username'],
                                                     action='read',
                                                     prefetch=('collections', 'comments', 'tags'))
    except DBPermissionError:
        raise HTTPPermissionError(request)

    try:
        with (setdir / 'detail.json').open() as f:
            detail = json.load(f)  # pylint: disable=redefined-outer-name
    except IOError:
        raise web.HTTPNotFound()

    dataset = query[0]  # pylint: disable=redefined-outer-name
    detail.update({
        'acl': get_local_granted(request),
        'collection': dataset.collections[0].name,
        'id': dataset.id,
        'setid': str(dataset.setid),
        'comments': [{'author': x.author, 'text': x.text, 'timeAdded': x.time_added}
                     for x in sorted(dataset.comments, key=lambda x: x.time_added)],
        'tags': [x.value for x in sorted(dataset.tags, key=lambda x: x.value)],
        'all_known_tags':
            await site.db.get_all_known_tags_for_collection(dataset.collections[0].name),
    })

    resp = web.json_response(detail, headers={'Cache-Control': 'no-cache'})
    return resp


async def _get_filepath(request, setid, setdir, path):
    if path.isdigit():
        try:
            pathstr = await request.app['site'].db.get_filepath_by_setid_idx(
                setid,
                int(path),
                user=request['username'],
            )
        except DBPermissionError:
            raise HTTPPermissionError(request)
        path = Path(pathstr)

    else:
        try:
            await request.app['site'].db.get_datasets_by_setids([setid], [],
                                                                user=request['username'],
                                                                action='read')
        except DBPermissionError:
            raise HTTPPermissionError(request)
        path = safejoin(setdir, path)

    # Make sure path exists and is safe
    if not path.is_absolute() or not path.is_file():
        raise web.HTTPNotFound()
    return path


@dataset.endpoint('/dataset/{setid:[^/]+}{_:/?}{path:((?<=/).*)?}', acl_key='read')
async def detail(request):
    setid = request.match_info['setid']
    path = request.match_info['path'] or 'detail.json'
    try:
        setid = str(SetID(setid))
    except ValueError:
        raise web.HTTPBadRequest()

    setdir = Path(request.app['site'].config.marv.storedir) / setid

    if path == 'detail.json':
        return await _send_detail_json(request, setid, setdir)

    path = await _get_filepath(request, setid, setdir, path)

    headers = {
        'Cache-Control': 'no-cache',
        'Content-Disposition': f'attachment; filename={path.name}',
    }

    if request.app['site'].config.marv.reverse_proxy == 'nginx':
        mime = mimetypes.guess_type(str(path))[0]
        approot = request.path.split('/marv/api/dataset/')[0]
        return web.Response(headers={
            'Content-Type': mime or 'application/octet-stream',
            'X-Accel-Buffering': 'no',
            'X-Accel-Redirect': f'{approot}{str(path)}',
            **headers,
        })

    return web.FileResponse(path, headers=headers)
