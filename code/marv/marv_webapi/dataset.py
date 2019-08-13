# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import json
import mimetypes
import pathlib

from aiohttp import web

from marv.model import Comment, Dataset, File, Tag, dataset_tag, scoped_session
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

    with scoped_session(request.app['site']) as session:
        query = session.query(File.path)\
                       .filter(File.dataset_id.in_(ids))\
                       .order_by(File.path)
        paths = [x[0] for x in query]

        query = session.query(Dataset.setid, File.idx)\
                       .filter(Dataset.id.in_(ids))\
                       .join(File)\
                       .order_by(Dataset.setid)
    urls = [f'dataset/{setid}/{idx}' for setid, idx in query]

    # TODO: complain about invalid/unknown ids?

    return web.json_response({'paths': paths, 'urls': urls})


def _send_detail_json(request, setid, setdir):
    try:
        with (setdir / 'detail.json').open() as f:
            detail = json.load(f)  # pylint: disable=redefined-outer-name
    except IOError:
        raise web.HTTPNotFound()

    # TODO: investigate merge into one
    with scoped_session(request.app['site']) as session:
        dataset_id, collection = session.query(Dataset.id, Dataset.collection)\
                                        .filter(Dataset.setid == setid)\
                                        .one()
        comments = session.query(Comment.author, Comment.time_added, Comment.text)\
                          .filter(Comment.dataset_id == dataset_id)\
                          .order_by(Comment.time_added)
        detail['comments'] = [{'author': x[0],
                               'timeAdded': x[1],
                               'text': x[2]} for x in comments]

        collection = request.app['site'].collections[collection]
        alltags = session.query(Tag.value)\
                         .filter(Tag.collection == collection.name)\
                         .order_by(Tag.value)
        detail['all_known_tags'] = [x[0] for x in alltags]

        tags = session.query(Tag.value)\
                      .join(dataset_tag)\
                      .filter(dataset_tag.c.dataset_id == dataset_id)\
                      .order_by(Tag.value)
    detail['tags'] = [x[0] for x in tags]
    detail['collection'] = collection.name
    detail['id'] = dataset_id
    detail['setid'] = setid
    resp = web.json_response(detail)
    resp.headers['Cache-Control'] = 'no-cache'
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
        return _send_detail_json(request, setid, setdir)

    if path.isdigit():
        with scoped_session(request.app['site']) as session:
            path = pathlib.Path(session.query(File.path)
                                .join(Dataset)
                                .filter(Dataset.setid == setid)
                                .filter(File.idx == int(path))
                                .scalar())
    else:
        path = setdir / path
        if '..' in path.parts:
            raise web.HTTPBadRequest()

    # Make sure path exists and is safe
    if not path.is_absolute() \
       or not path.is_file():
        raise web.HTTPNotFound()

    if request.app['site'].config.marv.reverse_proxy == 'nginx':
        mime = mimetypes.guess_type(path)
        return web.Response(headers={
            'content-type': mime[0] if mime[0] else 'application/octet-stream',
            'cache-control': 'no-cache',
            'x-accel-buffering': 'no',
            'x-accel-redirect': request.url,
            'Content-Disposition': f'attachment; filename={path.name}',
        })

    try:
        return web.FileResponse(path, headers={
            'Cache-Control': 'no-cache',
            'Content-Disposition': f'attachment; filename={path.name}',
        })
    except ValueError:
        raise web.HTTPNotFound()
