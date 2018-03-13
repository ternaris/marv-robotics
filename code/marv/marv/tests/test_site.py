# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import inspect
import os
import random
import shutil
import tempfile
import unittest
from itertools import count
from logging import getLogger

import marv.app
import marv.model
from marv.model import db
from marv.site import Site


KEEP = os.environ.get('KEEP')
log = getLogger(__name__)


def scan_foo(directory, subdirs, filenames):
    return [(os.path.basename(x), [x]) for x in filenames
            if x.endswith('.foo')]


def scan_bar(directory, subdirs, filenames):
    return [(os.path.basename(x), [x]) for x in filenames
            if x.endswith('.bar')]


class TestCase(unittest.TestCase):
    CONFIG = """
    [marv]
    collections = foo bar

    [collection foo]
    scanner = marv.tests.test_site:scan_foo
    scanroots = scanroot/foo

    [collection bar]
    scanner = marv.tests.test_site:scan_bar
    scanroots = scanroot/bar
    """
    counter = count()

    def setUp(self):
        self.sitedir = sitedir = tempfile.mkdtemp()
        self.scanroot = scanroot = os.path.join(sitedir, 'scanroot')
        os.mkdir(scanroot)
        os.mkdir(os.path.join(scanroot, 'foo'))
        os.mkdir(os.path.join(scanroot, 'bar'))
        self.siteconf = siteconf = os.path.join(sitedir, 'marv.conf')
        with open(siteconf, 'w') as f:
            f.write(inspect.cleandoc(self.CONFIG))

        prefix = 'test{}_'.format(self.counter.next())
        marv.model._LISTING_PREFIX
        marv.model._LISTING_PREFIX = prefix
        self.site = Site(siteconf)

        app = marv.app.create_app(self.site)
        appctx = app.app_context()
        appctx.push()

        def cleanup():
            appctx.pop()
            db.session.remove()
            del self.site
            for table in [v for k, v in db.metadata.tables.items()
                          if k.startswith(prefix)]:
                db.metadata.remove(table)
            if not KEEP:
                shutil.rmtree(sitedir)
            else:
                print('Keeping {}'.format(sitedir))
        self.cleanup = cleanup

    def tearDown(self):
        self.cleanup()

    def generate_foo(self, name):
        filename = os.path.join(self.scanroot, 'foo', '{}.foo'.format(name))
        with open(filename, 'w') as f:
            f.write('')
        log.verbose('wrote %s', filename)
        return filename

    def generate_bar(self, name):
        filename = os.path.join(self.scanroot, 'bar', '{}.bar'.format(name))
        with open(filename, 'w') as f:
            f.write('')
        log.verbose('wrote %s', filename)
        return filename

    def test_flow_query_and_tag(self):
        # init and scan empty
        site = self.site
        site.init()
        site.scan()
        self.assertEqual(site.query(), [])

        # generate some
        random.seed(42)
        foo1 = self.generate_foo('foo1')
        foo2 = self.generate_foo('foo2')
        bar1 = self.generate_bar('bar1')
        site.scan()
        self.assertEqual(site.query(), ['k5jgqruqhoyt5xsweq46tqnyem',
                                        'tv43di37ggabzui2m4dpwqgwxu',
                                        'vfqitpfhd46ru3jnhsw3gzu4xu'])

        # generate more and rescan
        foo3 = self.generate_foo('foo3')
        bar2 = self.generate_bar('bar2')
        site.scan()
        self.assertEqual(len(site.query()), 5)

        # get ids
        foo1id = site.query(path=foo1)[0]
        foo2id = site.query(path=foo2)[0]
        foo3id = site.query(path=foo3)[0]
        bar1id = site.query(path=bar1)[0]
        bar2id = site.query(path=bar2)[0]

        # query combinations
        self.assertEqual(set(site.query(collections=['bar'])), {bar1id, bar2id})
        self.assertEqual(site.query(path=foo1[:-1]), [foo1id])
        self.assertEqual(site.query(collections=['bar'], path=foo1[:-1]), [])
        self.assertEqual(site.query(collections=['foo', 'bar'], path=foo1), [foo1id])

        # tag
        self.site.tag([foo1id, foo2id, bar1id], add=['a', 'b'])
        self.site.tag([foo3id], add=['c'])
        self.assertEqual(site.listtags(), ['a', 'b', 'c'])
        self.assertEqual(site.listtags(collections=['foo']), ['a', 'b', 'c'])
        self.assertEqual(site.listtags(collections=['bar']), ['a', 'b'])

        # query tagged
        self.assertEqual(set(site.query(tags=['a'])), {foo1id, foo2id, bar1id})
        self.assertEqual(set(site.query(tags=['b', 'c'])),
                         {foo1id, foo2id, foo3id, bar1id})

        # untag
        self.site.tag([foo1id, bar1id, bar2id], add=['x'], remove=['a', 'b'])
        self.assertEqual(site.listtags(), ['a', 'b', 'c', 'x'])
        self.assertEqual(site.listtags(collections=['foo']), ['a', 'b', 'c', 'x'])
        self.assertEqual(site.listtags(collections=['bar']), ['a', 'b', 'x'])
        self.assertEqual(site.query(path=foo1, tags=['a']), [])
        self.assertEqual(site.query(path=foo2, tags=['a']), [foo2id])
        self.site.tag([foo1id], remove=['x'])

        # cleanup tags
        self.site.cleanup_tags()
        self.assertEqual(site.listtags(), ['a', 'b', 'c', 'x'])
        self.assertEqual(site.listtags(collections=['foo']), ['a', 'b', 'c'])
        self.assertEqual(site.listtags(collections=['bar']), ['x'])

        # run nodes
        self.site.run(foo1id)

    def test_outdated_node(self):
        site = self.site

        site.init()
        foo1 = self.generate_foo('foo1')
        site.scan()
        foo1id = site.query(path=foo1)[0]
