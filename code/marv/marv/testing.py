# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import os
import shutil
import tempfile
import unittest
from contextlib import contextmanager


@contextmanager
def chdir(d):
    """Change working directory - NOT THREAD SAFE"""
    cwd = os.getcwd()
    os.chdir(d)
    try:
        yield d
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
    """Create, change into, and cleanup temporary directory"""
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


class TestCase(unittest.TestCase):
    """Basic marv test case"""
    KEEP_TEST_DIR = None
    test_dir = None

    def run(self, result=None):
        with temporary_directory(self.KEEP_TEST_DIR) as tmpdir:
            self.test_dir = tmpdir
            super(TestCase, self).run(result)
