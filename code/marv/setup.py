# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import io
import os
from collections import OrderedDict

from setuptools import find_packages, setup

NAME = 'marv'
VERSION = '21.08.0'
DESCRIPTION = 'MARV framework'
ENTRY_POINTS = {
    'marv_cli': ['marv = marv.cli'],
    'marv_stream': ['messages = marv_ros_stream:messages'],
}

# Copy/paste block below here

os.chdir(os.path.abspath(os.path.dirname(__file__)))

with io.open(os.path.join('README.rst'), 'rt', encoding='utf8') as f:
    README = f.read()

with io.open('requirements.in', 'rt', encoding='utf8') as f:
    INSTALL_REQUIRES = [
        # e.g. -r ../path/to/file/package_name.in
        f'{os.path.basename(req.split()[1])[:-3]}=={VERSION}' if req.startswith('-r') else req
        for req in [line.strip() for line in f.readlines() if not line.startswith('#')]
        if req
    ]

setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      long_description=README,
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'License :: OSI Approved :: GNU Affero General Public License v3',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 3 :: Only',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python',
          'Topic :: Scientific/Engineering',
      ],
      author='Ternaris',
      author_email='team@ternaris.com',
      maintainer='Ternaris',
      maintainer_email='team@ternaris.com',
      url='https://ternaris.com/marv-robotics',
      project_urls=OrderedDict((
          ('Documentation', 'https://ternaris.com/marv-robotics/docs/'),
          ('Code', 'https://gitlan.com/ternaris/marv-robotics'),
          ('Issue tracker', 'https://gitlab.com/ternaris/marv-robotics/issues'),
      )),
      license='AGPL-3.0-only',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      python_requires='>=3.8.2',
      install_requires=INSTALL_REQUIRES,
      tests_require=[
          'pytest',
          'testfixtures',
      ],
      setup_requires=['pytest-runner'],
      entry_points=ENTRY_POINTS)
