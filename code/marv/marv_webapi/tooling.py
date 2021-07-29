# Copyright 2016 - 2021  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import math
import mimetypes
import os
import time
from datetime import timezone
from pathlib import Path

import jwt
from aiohttp import web
from aiohttp.web_urldispatcher import SystemRoute

AGGRESSIVE_CACHING = bool(os.environ.get('MARV_EXPERIMENTAL_AGGRESSIVE_CACHING'))


@web.middleware
async def auth_middleware(request, handler):
    if (instance := getattr(handler, '__self__', None)) and isinstance(instance, SystemRoute):  # pylint: disable=used-before-assignment
        return await handler(request)

    assert isinstance(handler.acl, set)
    authorization = request.headers.get('Authorization')
    if not authorization:
        authorization = request.query.get('access_token')

    username = 'marv:anonymous'
    groups = {'__unauthenticated__'}
    if authorization:
        token = authorization.replace('Bearer ', '')
        try:
            session = jwt.decode(token, request.app['config']['SECRET_KEY'], algorithms=['HS256'])
        except BaseException:
            raise web.HTTPUnauthorized()

        user = await request.app['site'].db.get_user_by_name(session['sub'], deep=True)
        if not user or not user.active \
                or user.time_updated.replace(tzinfo=timezone.utc).timestamp() > session['iat']:
            raise web.HTTPUnauthorized()

        username = user.name
        groups = {g.name for g in user.groups}
        groups.add('__authenticated__')

        if '__authenticated__' not in handler.acl:
            raise web.HTTPForbidden()

    elif '__unauthenticated__' not in handler.acl:
        raise web.HTTPUnauthorized()

    request['username'] = username
    request['user_groups'] = groups

    return await handler(request)


def HTTPPermissionError(request):  # pylint: disable=invalid-name
    if request['username'] == 'marv:anonymous':
        return web.HTTPUnauthorized
    return web.HTTPForbidden


def get_global_granted(request):
    if 'admin' in request['user_groups']:
        return ['admin']
    return []


def get_local_granted(request):
    if request['username'] == 'marv:anonymous':
        if request.app['site'].config.marv.ce_anonymous_readonly_access:
            return ['download_raw', 'list', 'read']
        return []

    if 'admin' in request['user_groups']:
        return ['comment', 'delete', 'download_raw', 'list', 'read', 'tag']
    return ['comment', 'download_raw', 'list', 'read', 'tag']


def generate_token(username, key):
    now = math.ceil(time.time())
    return jwt.encode({
        'exp': now + 2419200,  # 4 weeks expiration
        'iat': now,
        'sub': username,
    }, key, algorithm='HS256')


def safejoin(basepath, rel):
    rel = Path(rel)
    if rel.anchor:
        raise web.HTTPForbidden

    fullpath = basepath.joinpath(rel).resolve()
    if basepath.resolve() not in fullpath.parents:
        raise web.HTTPForbidden

    return fullpath


def sendfile(path, approot, reverse_proxy, filename=None, headers=None):
    headers = headers.copy() if headers else {}
    headers.setdefault('Content-Disposition', f'attachment; filename={filename or path.name}')

    if AGGRESSIVE_CACHING and (
            path.suffix in ('.jpg', '.json')
            or (path.suffix == '.mrv' and path.stat().st_size < 20 * 10**6)
            or path.name == 'default-stream'
    ):
        headers['Cache-Control'] = 'max-age=14400'
    else:
        headers['Cache-Control'] = 'no-cache, no-store'

    if reverse_proxy == 'nginx':
        mime = mimetypes.guess_type(str(path))[0]
        return web.Response(headers={
            'Content-Type': mime or 'application/octet-stream',
            'X-Accel-Buffering': 'no',
            'X-Accel-Redirect': f'{approot}{str(path)}',
            **headers,
        })

    assert not reverse_proxy, f'Unknown reverse_proxy {reverse_proxy}'
    return web.FileResponse(path, headers=headers)


class Webapi:
    def __init__(self, url_prefix=''):
        self.url_prefix = url_prefix
        self.endpoints = []

    def endpoint(self, url_rule, methods, only_anon=False, allow_anon=False):
        def closure(func):
            func.name = func.__name__
            func.url_rule = f'{self.url_prefix}{url_rule}'
            if only_anon:
                func.acl = {'__unauthenticated__'}
            else:
                func.acl = {'__authenticated__'}
                if allow_anon:
                    func.acl |= {'__unauthenticated__'}
            func.methods = methods
            self.endpoints.append(func)
        return closure

    def __repr__(self):
        return f'<Webapi url_prefix={self.url_prefix}>'
