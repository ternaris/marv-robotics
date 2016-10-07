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
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
# with open(os.path.join(here, 'CHANGES.txt')) as f:
#     CHANGES = f.read()

REQUIRES = [
    'marv-server',
    'matplotlib',
    'pillow',
    'utm',
    ]

setup(name='marv-robotics',
      version='2.0.0b1',
      description='Data management platform for robot logs',
      long_description=README,
      # long_description=README + '\n\n' + CHANGES,
      classifiers=[
          'Development Status :: 4 - Beta',
          #'Development Status :: 5 - Production/Stable',
          'License :: OSI Approved :: Apache Software License',
          'Operating System :: POSIX :: Linux',  # for now
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 2 :: Only',  # for now
          'Programming Language :: Python :: Implementation :: CPython',  # for now
          'Topic :: Scientific/Engineering',
      ],
      author='Ternaris',
      author_email='team@ternaris.com',
      url='https://ternaris.com/marv-robotics',
      license='Apache License 2.0',
      keywords=[],
      packages=['marv_robotics', 'marv_robotics.tests', 'marv_robotics.nodes'],
      include_package_data=True,
      zip_safe=False,
      test_suite='nose.collector',
      tests_require=['nose'],
      install_requires=REQUIRES,
      entry_points={'marv_profiles': ['robotics = marv_robotics:marv_profile']})
