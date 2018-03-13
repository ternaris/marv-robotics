# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

from .auth import auth
from .comment import comment
from .dataset import dataset
from .delete import delete
from .tag import tag
from .collection import collection, meta
from .tooling import api_group as marv_api_group


@marv_api_group()
def webapi(app):
    pass


# Groups and endpoints are all the same for now
webapi.add_endpoint(auth)
webapi.add_endpoint(comment)
webapi.add_endpoint(dataset)
webapi.add_endpoint(delete)
webapi.add_endpoint(collection)
webapi.add_endpoint(meta)
webapi.add_endpoint(tag)
