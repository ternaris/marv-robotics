# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import os

from capnp.lib.capnp import KjException

import marv_api as marv
from marv_api.setid import SetID
from marv_api.utils import err
from marv_detail import Widget
from marv_pycapnp import Wrapper

from .types_capnp import Dataset  # pylint: disable=import-error


@marv.node(Dataset)
def dataset():
    raise RuntimeError('Datasets are added not run')
    yield  # pylint: disable=unreachable


def load_dataset(setdir, dataset):  # pylint: disable=redefined-outer-name
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
        wrapper = Wrapper.from_dict(Dataset, dct, setdir=setdir)
    except KjException as e:
        from pprint import pformat  # pylint: disable=import-outside-toplevel
        err('Schema violation for %s with data:\n%s\nschema: %s' % (
            Dataset.schema.node.displayName,
            pformat(dct),
            Dataset.schema.node.displayName))
        raise e
    return [wrapper]


dataset.load = load_dataset


@marv.node(Widget)
@marv.input('dataset', default=dataset)
def summary_keyval(dataset):  # pylint: disable=redefined-outer-name
    dataset = yield marv.pull(dataset)
    if len(dataset.files) < 2:
        return
    yield marv.push({'keyval': {
        'items': [
            {'title': 'size', 'formatter': 'filesize', 'list': False,
             'cell': {'uint64': sum(x.size for x in dataset.files)}},
            {'title': 'files', 'list': False,
             'cell': {'uint64': len(dataset.files)}},
        ],
    }})


@marv.node(Widget)
@marv.input('dataset', default=dataset)
def meta_table(dataset):  # pylint: disable=redefined-outer-name
    dataset = yield marv.pull(dataset)
    columns = [
        {'title': 'Name', 'formatter': 'rellink', 'sortkey': 'title'},
        {'title': 'Size', 'formatter': 'filesize'},
    ]
    # dataset.id is setid here
    rows = [
        {
            'id': idx,
            'cells': [
                {'link': {
                    'href': f'{idx}',
                    'title': os.path.basename(f.path),
                }},
                {'uint64': f.size},
            ],
        }
        for idx, f in enumerate(dataset.files)
    ]
    yield marv.push({'table': {'columns': columns, 'rows': rows}})
