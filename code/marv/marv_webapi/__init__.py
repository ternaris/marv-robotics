# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from pkg_resources import iter_entry_points

from .auth import auth
from .collection import collection, meta
from .comment import comment
from .dataset import dataset as dataset_api
from .delete import delete
from .rpcs import rpcs
from .tag import tag
from .tooling import api_group as marv_api_group


@marv_api_group()
def webapi(_):
    pass


# Groups and endpoints are all the same for now
webapi.add_endpoint(auth)
webapi.add_endpoint(comment)
webapi.add_endpoint(dataset_api)
webapi.add_endpoint(delete)
webapi.add_endpoint(collection)
webapi.add_endpoint(meta)
webapi.add_endpoint(rpcs)
webapi.add_endpoint(tag)


def load_entry_points():
    for entry_point in iter_entry_points(group='marv_webapi'):
        endpoint = entry_point.load()
        webapi.add_endpoint(endpoint)
