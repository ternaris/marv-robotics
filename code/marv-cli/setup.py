# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import io
import re
import os
from collections import OrderedDict
from setuptools import find_packages, setup

NAME = 'marv-cli'
DESCRIPTION = 'Core of the MARV command-line interface'
ENTRY_POINTS = {
    'console_scripts': [
        'marv = marv_cli:cli',
        'marv-ipdb = marv_cli:cli_ipdb',
    ],
}
INTERNAL_REQUIRES = [
]

# Copy/paste block below here

os.chdir(os.path.abspath(os.path.dirname(__file__)))

with io.open(os.path.join('README.rst'), 'rt', encoding='utf8') as f:
    README = f.read()

with io.open(os.path.join(NAME.replace('-', '_'), '__init__.py'), encoding='utf8') as f:
    VERSION = re.search(r'__version__ = \'(.*?)\'', f.read()).group(1)

with io.open('requirements.in', 'rt', encoding='utf8') as f:
    INSTALL_REQUIRES = [
        x for x in
        [x.strip() for x in f.readlines()]
        if x
        if not x.startswith('-r')
        if not x[0] == '#'
    ] + ['{}=={}'.format(x, VERSION) for x in INTERNAL_REQUIRES]

setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      long_description=README,
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Framework :: Flask',
          'License :: OSI Approved :: GNU Affero General Public License v3',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 2 :: Only',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python',
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
          'Topic :: Scientific/Engineering',
      ],
      author='Ternaris',
      author_email='team@ternaris.com',
      maintainer='Ternaris',
      maintainer_email='team@ternaris.com',
      url='https://ternaris.com/marv-robotics',
      project_urls=OrderedDict((
          ('Documentation', 'https://ternaris.com/marv-robotics/docs/'),
          ('Code', 'https://github.com/ternaris/marv-robotics'),
          ('Issue tracker', 'https://github.com/ternaris/marv-robotics/issues'),
      )),
      license='AGPL-3.0-only',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      python_requires='>=2.7.12,<3.0',
      install_requires=INSTALL_REQUIRES,
      tests_require=[
          'pytest',
          'mock',
          'testfixtures',
      ],
      setup_requires=['pytest-runner'],
      entry_points=ENTRY_POINTS)
