# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

from collections import OrderedDict

import flask
from flask import current_app, request


class APIEndpoint(object):
    MIN_API_VERSION = 3
    LATEST_API_VERSION = 3
    HEADER_PREFIX = "application/vnd.marv.v"
    acl = None

    def __init__(self, name, func, url_rule, defaults=None, methods=None, version=None, force_acl=None):
        self.name = name
        version = self.MIN_API_VERSION if version is None else version
        self.funcs = [(version, func)]
        self.url_rules = [(url_rule, {'defaults': defaults, 'methods': methods})]
        self._force_acl = set(force_acl) if force_acl else None

    def __call__(self, *args, **kw):
        authorization = request.headers.get('Authorization')
        # TODO: can authorization be '' or is None test?
        if not authorization:
            authorization = request.args.get('access_token')
        groups = current_app.um.check_authorization(self.acl, authorization)

        try:
            accepted = (x[0] for x in flask.request.accept_mimetypes
                        if x[0].startswith(self.HEADER_PREFIX)).next()
            accepted_version = int(accepted[len(self.HEADER_PREFIX):])
        except (StopIteration, ValueError):
            accepted_version = self.MIN_API_VERSION

        try:
            func = (func for version, func in self.funcs
                    if version <= accepted_version).next()
        except StopIteration:
            flask.abort(406)

        return func(*args, **kw)

    def init_app(self, app, url_prefix=None, name_prefix=None):
        self.acl = self._force_acl if self._force_acl else set(current_app.acl[self.name])
        name = '.'.join(filter(None, [name_prefix, self.name]))
        for url_rule, options in self.url_rules:
            url_rule = ''.join(filter(None, [url_prefix, url_rule]))
            app.add_url_rule(url_rule, name, self, **options)


class APIGroup(object):
    def __init__(self, name, func, url_prefix=None):
        self.name = name
        self.func = func
        self.url_prefix = url_prefix
        self.endpoints = OrderedDict()

    def add_endpoint(self, ep):
        """endpoints and groups are all the same (for now)"""
        assert ep.name not in self.endpoints, ep
        self.endpoints[ep.name] = ep

    def endpoint(self, *args, **kw):
        return api_endpoint(*args, registry=self.endpoints, **kw)

    def init_app(self, app, url_prefix=None, name_prefix=None):
        self.func(app)
        name_prefix = '.'.join(filter(None, [name_prefix, self.name]))
        url_prefix = '/'.join(filter(None, [url_prefix, self.url_prefix])) or None
        for ep in self.endpoints.values():
            ep.init_app(app, url_prefix=url_prefix, name_prefix=name_prefix)

    def __repr__(self):
        return '<APIGroup {} url_prefix={}>'.format(self.name, self.url_prefix)


def api_endpoint(url_rule, defaults=None, methods=None, version=None,
                 cls=APIEndpoint, registry=None, force_acl=None):
    def decorator(func):
        if isinstance(func, cls):
            func.url_rules.append((url_rule, {'defaults': defaults, 'methods': methods}))
            return func

        name = func.func_name
        rv = cls(name, func, url_rule=url_rule, defaults=defaults,
                 methods=methods, version=version, force_acl=force_acl)
        rv.__doc__ = func.__doc__

        if registry is not None:
            assert name not in registry, name
            registry[name] = rv
        return rv
    return decorator


def api_group(url_prefix=None, cls=APIGroup):
    def decorator(func):
        if isinstance(func, cls):
            raise TypeError('Attempted to convert function into api group twice.')

        name = func.func_name
        rv = cls(name, func, url_prefix)
        rv.__doc__ = func.__doc__
        return rv
    return decorator
