# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only


def download_link(file, dataset):
    return {
        'href': f'download/{dataset.files.index(file)}',
        'target': '_blank',
        'title': file.relpath,
    }


def file_status(file):
    state = []
    if file and file.missing:
        state.append({'icon': 'hdd',
                      'title': 'This file is missing',
                      'classes': 'text-danger'})
    return state
