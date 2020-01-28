# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import os
import shutil
import tempfile
from contextlib import contextmanager


@contextmanager
def chdir(directory):
    """Change working directory - NOT THREAD SAFE."""
    cwd = os.getcwd()
    os.chdir(directory)
    try:
        yield directory
    finally:
        os.chdir(cwd)


def make_scanroot(scanroot, names):
    if not os.path.exists(scanroot):
        os.makedirs(scanroot)
    for name in names:
        with open(os.path.join(scanroot, name), 'w') as f:
            f.write(name)


@contextmanager
def temporary_directory(keep=None):
    """Create, change into, and cleanup temporary directory."""
    tmpdir = tempfile.mkdtemp()
    with chdir(tmpdir):
        try:
            yield tmpdir
        finally:
            if not keep:
                shutil.rmtree(tmpdir)


def decode(data, encoding='utf-8'):
    if isinstance(data, str):
        data = data.decode(encoding)
    elif isinstance(data, dict):
        data = {decode(k): decode(v) for k, v in data.items()}
    elif isinstance(data, list):
        data = [decode(x) for x in data]
    elif isinstance(data, tuple):
        data = tuple(decode(x) for x in data)
    return data
