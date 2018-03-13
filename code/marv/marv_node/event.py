# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function


from collections import OrderedDict


class DefaultOrderedDict(OrderedDict):
    def __init__(self, factory):
        super(DefaultOrderedDict, self).__init__()
        self._factory = factory

    def __getitem__(self, key):
        try:
            return super(DefaultOrderedDict, self).__getitem__(key)
        except KeyError:
            value = self._factory()
            self[key] = value
            return value
