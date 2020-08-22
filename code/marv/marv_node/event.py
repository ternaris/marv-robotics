# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only


from collections import OrderedDict


class DefaultOrderedDict(OrderedDict):
    def __init__(self, factory):
        super().__init__()
        self._factory = factory

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            value = self._factory()
            self[key] = value
            return value
