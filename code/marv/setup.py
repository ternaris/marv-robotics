# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import os
from setuptools import setup

HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, 'README.rst')) as f:
    README = f.read()


with open(os.path.join(HERE, 'requirements.in')) as f:
    INSTALL_REQUIRES = [x for x in
                        [x.strip() for x in f.readlines()]
                        if x
                        if not x.startswith('-r')
                        if not x[0] == '#']
INSTALL_REQUIRES.extend([
    'marv-cli==3.0.0'
])


setup(name='marv',
      version='3.2.0',
      description='MARV framework',
      long_description=README,
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Framework :: Flask',
          'License :: OSI Approved :: GNU Affero General Public License v3',
          'Operating System :: POSIX :: Linux',  # for now
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 2 :: Only',  # for now
          'Programming Language :: Python :: Implementation :: CPython',  # for now
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
          'Topic :: Scientific/Engineering',
      ],
      author='Ternaris',
      author_email='team@ternaris.com',
      url='https://ternaris.com/marv-robotics',
      license='AGPL-3.0-only',
      packages=[
          'marv',
          'marv.app',
          'marv.tests',
          'marv_detail',
          'marv_node',
          'marv_node.testing',
          'marv_node.tests',
          'marv_nodes',
          'marv_pycapnp',
          'marv_pycapnp.tests',
          'marv_store',
          'marv_webapi',
      ],
      include_package_data=True,
      zip_safe=False,
      tests_require=[
          'pytest',
          'mock',
          'testfixtures',
      ],
      setup_requires=['pytest-runner'],
      install_requires=INSTALL_REQUIRES,
      entry_points={'marv_cli': ['marv = marv.cli']})
