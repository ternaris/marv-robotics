# -*- coding: utf-8 -*-
#
# This file is part of MARV Robotics
#
# Copyright 2016 Ternaris
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function

import os
import re
import unittest
from collections import defaultdict
from mock import patch

import marv
from marv import Site, create_app
from marv._model import Fileset, Fileinfo, db
from marv.testing import make_scanroot, temporary_directory

from marv_robotics import bagset


KEEP = os.getenv('KEEP')


def repr_mock(info, realrepr=Fileinfo.__repr__):
    """mock function for Fileinfo.__repr__"""
    return re.sub(r'mtime=\d+.\d+,', "mtime='MTIME'", realrepr(info))


@unittest.skip
class TestCase(unittest.TestCase):
    SQLALCHEMY_ECHO = False
    fqtn = 'marv_robotics.bagset'
    scanroot = './scanroot'
    site = None
    test_dir = None

    def run(self, result=None):
        with temporary_directory(KEEP) as tmpdir:
            self.test_dir = tmpdir
            self.site = site = Site(os.path.join(self.test_dir, 'marv.conf'))
            app = create_app(site, config_obj=self)
            app_context = app.app_context()
            app_context.push()
            db.create_all()

            self.site.config['collection'] = {'scanroot': self.scanroot,
                                          'fileset': self.fqtn}
            self.site.write_config()
            self.site.load_config()

            with patch.object(Fileinfo, '__repr__', new=repr_mock):
                super(TestCase, self).run(result)
            app_context.pop()

    def test_nonbag(self):
        make_scanroot(self.scanroot, ['foo'])
        ctx = self.site.scan()
        self.assertEqual(len(ctx.agg_added), 0)

    def test_single_bags(self):
        make_scanroot(self.scanroot, ['foo.bag', 'bar.bag'])
        ctx = self.site.scan()
        self.assertEqual(len(ctx.agg_added), 2)

        # scan again
        ctx = self.site.scan()
        self.assertEqual(len(ctx.agg_added), 0)

    def test_scan_same_prefix(self):
        make_scanroot(self.scanroot, ['set0_0000-00-00-00-00-00_0.bag',
                                      'set0_0000-00-00-00-00-00_1.bag',
                                      'set0_0000-00-00-00-00-00_2.bag',
                                      'set0_0000-11-00-00-00-00_0.bag',
                                      'set0_0000-11-00-00-00-00_1.bag',
                                      'set0_0000-11-00-00-00-00_2.bag'])
        ctx = self.site.scan()
        filesets = [x.fileset for x in ctx.agg_added.values()]
        self.assertEqual(sorted([x.files[-1].relpath for x in filesets]), [
            'set0_0000-00-00-00-00-00_2.bag',
            'set0_0000-11-00-00-00-00_2.bag',
        ])

        # scan again
        ctx = self.site.scan()
        self.assertEqual(len(ctx.agg_added), 0)

    def test_scan_broken_set_edge_cases(self):
        make_scanroot(self.scanroot, ['set0_0000-00-00-00-00-00_0.bag',
                                      'set0_0000-00-00-00-00-00_2.bag',
                                      'set1_0000-00-00-00-00-00_1.bag',
                                      'set1_0000-00-00-00-00-00_2.bag',
                                      'set2.bag',
                                      'set2_0000-00-00-00-00-00_1.bag',
                                      'set2_0000-00-00-00-00-00_2.bag'])
        ctx = self.site.scan()
        filesets = [x.fileset for x in ctx.agg_added.values()]
        self.assertEqual(sorted([x.files[-1].relpath for x in filesets]), [
            'set0_0000-00-00-00-00-00_0.bag',
            'set2.bag',
        ])

        # fix and scan again
        make_scanroot(self.scanroot, ['set0_0000-00-00-00-00-00_1.bag',
                                      'set1_0000-00-00-00-00-00_0.bag',
                                      'set2_0000-00-00-00-00-00_0.bag'])
        ctx = self.site.scan()
        filesets = Fileset.query.all()
        self.assertEqual(sorted([x.files[-1].relpath for x in filesets]), [
            'set0_0000-00-00-00-00-00_0.bag',
            'set1_0000-00-00-00-00-00_2.bag',
            'set2.bag',
            'set2_0000-00-00-00-00-00_2.bag',
        ])

    def test_missing_timestamp(self):
        make_scanroot(self.scanroot, ['foo_0.bag', 'foo_2.bag'])
        ctx = self.site.scan()
        self.assertEqual(len(ctx.agg_added), 2)

    def test_missing_index(self):
        make_scanroot(self.scanroot, ['foo_0000-11-00-00-00-00.bag',
                                      'foo_0000-22-00-00-00-00.bag'])
        ctx = self.site.scan()
        self.assertEqual(len(ctx.agg_added), 2)
