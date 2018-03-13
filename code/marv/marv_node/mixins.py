# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

from abc import ABCMeta, abstractproperty
from logging import getLogger


class Keyed(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def key(self):
        return None  #pragma: nocoverage

    def __cmp__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return cmp(self.key, other.key)

    def __hash__(self):
        return hash((type(self), self.key))

    def __repr__(self):
        return '<{} key={!r}>'.format(type(self).__name__, self.key)


class GenWrapperMixin(object):
    _gen = None

    @property
    def close(self):
        return self._gen.close

    @property
    def next(self):
        return self._gen.next

    @property
    def send(self):
        return self._gen.send

    @property
    def throw(self):
        return self._gen.throw


class LoggerMixin(object):
    @property
    def logdebug(self):
        return self.log.debug

    @property
    def lognoisy(self):
        return self.log.noisy

    @property
    def logverbose(self):
        return self.log.verbose

    @property
    def loginfo(self):
        return self.log.info

    @property
    def logwarn(self):
        return self.log.warn

    @property
    def logerror(self):
        return self.log.error

    @property
    def log(self):
        logkey = ('marv', type(self).__name__.lower())
        if hasattr(self, 'key'):
            logkey += ((str(self.setid.abbrev),
                        self.node.name,
                        self.node.specs_hash[:10]) +
                       tuple(unicode(x) for x in self.key[2:]))
        return getLogger('.'.join(logkey))


class Task(object):
    __metaclass__ = ABCMeta
    __slots__ = ()

    def __repr__(self):
        return type(self).__name__


class Request(object):
    __metaclass__ = ABCMeta
    __slots__ = ()

    def __repr__(self):
        return type(self).__name__
