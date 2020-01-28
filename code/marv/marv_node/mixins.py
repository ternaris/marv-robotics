# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from abc import ABCMeta, abstractproperty
from logging import getLogger


class Keyed(metaclass=ABCMeta):

    @abstractproperty
    def key(self):
        return None  # pragma: nocoverage

    def __lt__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.key < other.key

    def __le__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.key <= other.key

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.key == other.key

    def __ne__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.key != other.key

    def __ge__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.key >= other.key

    def __gt__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.key > other.key

    def __hash__(self):
        return hash((type(self), self.key))

    def __repr__(self):
        return f'<{type(self).__name__} key={self.key!r}>'


class AGenWrapperMixin:
    _agen = None

    @property
    def aclose(self):
        return self._agen.aclose

    @property
    def __anext__(self):
        return self._agen.__anext__

    @property
    def asend(self):
        return self._agen.asend

    @property
    def athrow(self):
        return self._agen.athrow


class GenWrapperMixin:
    _gen = None

    @property
    def close(self):
        return self._gen.close

    @property
    def __next__(self):
        return self._gen.__next__

    @property
    def send(self):
        return self._gen.send

    @property
    def throw(self):
        return self._gen.throw


class LoggerMixin:
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
                        self.node.specs_hash[:10])
                       + tuple(str(x) for x in self.key[2:]))
        return getLogger('.'.join(logkey))


class Task(metaclass=ABCMeta):  # pylint: disable=too-few-public-methods
    __slots__ = ()

    def __repr__(self):
        return type(self).__name__


class Request(metaclass=ABCMeta):  # pylint: disable=too-few-public-methods
    __slots__ = ()

    def __repr__(self):
        return type(self).__name__
