# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import math
import mimetypes
import os
import time
from collections import OrderedDict
from datetime import timezone
from pathlib import Path

import jwt
from aiohttp import web

AGGRESSIVE_CACHING = bool(os.environ.get('MARV_EXPERIMENTAL_AGGRESSIVE_CACHING'))


async def check_authorization(request, acl, authorization):
    username = 'marv:anonymous'
    groups = {'__unauthenticated__'}
    if authorization:
        token = authorization.replace('Bearer ', '')
        try:
            session = jwt.decode(token, request.app['config']['SECRET_KEY'], algorithms=['HS256'])
        except BaseException:
            raise web.HTTPUnauthorized()

        user = await request.app['site'].db.get_user_by_name(session['sub'], deep=True)
        if not user or user.time_updated.replace(tzinfo=timezone.utc).timestamp() > session['iat']:
            raise web.HTTPUnauthorized()

        username = user.name
        groups = {g.name for g in user.groups}
        groups.add('__authenticated__')

    elif '__unauthenticated__' not in acl:
        raise web.HTTPUnauthorized()

    if acl and not acl.intersection(groups):
        raise web.HTTPForbidden()

    request['username'] = username
    request['user_groups'] = groups


def HTTPPermissionError(request):  # pylint: disable=invalid-name
    if request['username'] == 'marv:anonymous':
        return web.HTTPUnauthorized
    return web.HTTPForbidden


def get_global_granted(request):
    granted = {
        view.acl_key
        for name, view in request.app['api_endpoints'].items()
        if isinstance(view, APIEndpoint)
        if view.acl.intersection(request['user_groups'])
    }
    return sorted(granted - set(request.app['route_acl'].keys()))


def get_local_granted(request):
    return sorted({
        key
        for key, groups in request.app['route_acl'].items()
        if set(groups).intersection(request['user_groups'])
    })


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


def sendfile(path, approot, reverse_proxy, filename=None):
    headers = {
        'Content-Disposition': f'attachment; filename={filename or path.name}',
    }
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


class APIEndpoint:
    MIN_API_VERSION = 3
    LATEST_API_VERSION = 3
    HEADER_PREFIX = 'application/vnd.marv.v'
    acl = None

    def __init__(self, name, func, url_rule, defaults=None, methods=None, version=None,
                 acl_key=None, force_acl=None):
        # pylint: disable=too-many-arguments
        self.name = name
        version = self.MIN_API_VERSION if version is None else version
        self.funcs = [(version, func)]
        self.url_rules = [(url_rule, {'defaults': defaults, 'methods': methods})]
        self.force_acl = set(force_acl) if force_acl else None
        self.acl_key = acl_key or name

    async def __call__(self, request):
        authorization = request.headers.get('Authorization')
        # TODO: can authorization be '' or is None test?
        if not authorization:
            authorization = request.query.get('access_token')
        await check_authorization(request, self.acl, authorization)

        try:
            accepted = next(x[0] for x in request.headers.getall('ACCEPT', [])
                            if x[0].startswith(self.HEADER_PREFIX))
            accepted_version = int(accepted[len(self.HEADER_PREFIX):])
        except (StopIteration, ValueError):
            accepted_version = self.MIN_API_VERSION

        try:
            func = next(func for version, func in self.funcs
                        if version <= accepted_version)
        except StopIteration:
            raise web.HTTPNotAcceptable()

        return await func(request)

    def init_app(self, app, url_prefix=None, name_prefix=None, app_root=None):
        self.acl = self.force_acl if self.force_acl else set(app['route_acl'][self.acl_key])
        name = '.'.join(filter(None, [name_prefix, self.name]))
        for url_rule, options in self.url_rules:
            url_rule = ''.join(filter(None, [url_prefix, url_rule]))
            if options['methods'] is None:
                options['methods'] = ['GET']
            assert len(options['methods']) == 1
            app['api_endpoints'][name] = self
            app.add_routes([web.route(options['methods'][0],
                                      f'{app_root}{url_rule}',
                                      self.__call__, name=name)])


class APIGroup:
    def __init__(self, name, func, url_prefix=None):
        self.name = name
        self.func = func
        self.url_prefix = url_prefix
        self.endpoints = OrderedDict()

    def add_endpoint(self, ep):
        """Endpoints and groups are all the same (for now)."""
        assert ep.name not in self.endpoints, ep
        self.endpoints[ep.name] = ep

    def endpoint(self, *args, **kw):
        return api_endpoint(*args, registry=self.endpoints, **kw)

    def init_app(self, app, url_prefix=None, name_prefix=None, app_root=None):
        self.func(app)
        name_prefix = '.'.join(filter(None, [name_prefix, self.name]))
        url_prefix = '/'.join(filter(None, [url_prefix, self.url_prefix])) or None
        for ep in self.endpoints.values():
            ep.init_app(app, url_prefix=url_prefix, name_prefix=name_prefix, app_root=app_root)

    def __repr__(self):
        return f'<APIGroup {self.name} url_prefix={self.url_prefix}>'


def api_endpoint(url_rule, defaults=None, methods=None, version=None,
                 cls=APIEndpoint, registry=None, acl_key=None, force_acl=None):
    # pylint: disable=too-many-arguments

    def decorator(func):
        if isinstance(func, cls):
            func.url_rules.append((url_rule, {'defaults': defaults, 'methods': methods}))
            return func

        name = func.__name__
        rv = cls(name, func, url_rule=url_rule, defaults=defaults,
                 methods=methods, version=version, acl_key=acl_key, force_acl=force_acl)
        rv.__doc__ = func.__doc__  # pylint: disable=attribute-defined-outside-init

        if registry is not None:
            assert name not in registry, name
            registry[name] = rv
        return rv
    return decorator


def api_group(url_prefix=None, cls=APIGroup):
    def decorator(func):
        if isinstance(func, cls):
            raise TypeError('Attempted to convert function into api group twice.')

        name = func.__name__
        rv = cls(name, func, url_prefix)
        rv.__doc__ = func.__doc__  # pylint: disable=attribute-defined-outside-init
        return rv
    return decorator
