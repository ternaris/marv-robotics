# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import os
import unittest

from . import Store
from marv_node.testing import temporary_directory
from marv_node.setid import SetID
from marv_nodes import dataset


SETID = SetID(42)


@unittest.skip
class TestCase(unittest.TestCase):
    def test(self):
        with temporary_directory() as tmpdir:
            scanroot = os.path.join(tmpdir, 'scanroot')
            os.mkdir(scanroot)
            file1 = os.path.join(scanroot, 'file1')
            file2 = os.path.join(scanroot, 'file2')
            with open(file1, 'w') as f:
                f.write('1')
            with open(file2, 'w') as f:
                f.write('10')

            storedir = os.path.join(tmpdir, 'store')
            os.mkdir(storedir)
            store = Store(storedir)
            store.add_dataset(SETID, 'testset', [file1, file2])

            reader = store[(dataset, SETID)]
            self.assertEqual(reader.key, 'dataset')
            self.assertEqual(repr(reader),
                             '<Reader fiaaaaaaaaaaaaaaaaaaaaaaaa/dataset-1>')
