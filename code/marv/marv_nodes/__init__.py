# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import os
import sys

from capnp.lib.capnp import KjException

import marv
from marv_detail import Widget
from marv_node.setid import SetID
from marv_pycapnp import Wrapper
from .types_capnp import Dataset


@marv.node(Dataset)
def dataset():
    raise RuntimeError('Datasets are added not run')
    yield


def load_dataset(setdir, dataset):
    setid = SetID(dataset.setid)
    files = [{'path': x.path,
              'missing': bool(x.missing),
              'mtime': x.mtime * 10**6,
              'size': x.size} for x in sorted(dataset.files, key=lambda x: x.idx)]
    dct = {'id': setid,
           'name': dataset.name,
           'files': files,
           'time_added': dataset.time_added * 10**6,
           'timestamp': dataset.timestamp * 10**6}
    try:
        wrapper = Wrapper.from_dict(Dataset, dct)
    except KjException as e:
        from pprint import pformat
        print('Schema violation for %s with data:\n%s\nschema: %s' % (
            Dataset.schema.node.displayName,
            pformat(dct),
            Dataset.schema.node.displayName), file=sys.stderr)
        raise e
    wrapper._setdir = setdir  # needed by dataset.load(node)
    return [wrapper]
dataset.load = load_dataset


@marv.node(Widget)
@marv.input('dataset', default=dataset)
def summary_keyval(dataset):
    dataset = yield marv.pull(dataset)
    if len(dataset.files) < 2:
        return
    yield marv.push({'keyval': {
        'items': [
            {'title': 'size', 'formatter': 'filesize', 'list': False,
             'cell': {'uint64': sum(x.size for x in dataset.files)}},
            {'title': 'files', 'list': False,
             'cell': {'uint64': len(dataset.files)}},
        ]
    }})


@marv.node(Widget)
@marv.input('dataset', default=dataset)
def meta_table(dataset):
    dataset = yield marv.pull(dataset)
    columns = [
        {'title': 'Name', 'formatter': 'rellink'},
        {'title': 'Size', 'formatter': 'filesize'},
    ]
    # dataset.id is setid here
    rows = [{'id': idx, 'cells': [
        {'link': {'href': '{}'.format(idx),
                  'title': os.path.basename(f.path)}},
        {'uint64': f.size},
    ]} for idx, f in enumerate(dataset.files)]
    yield marv.push({'table': {'columns': columns, 'rows': rows}})
