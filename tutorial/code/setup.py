# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: CC0-1.0

from setuptools import setup

setup(
    name='marv-tutorial-code',
    version='1.0',
    description='MARV Tutorial Code',
    url='',
    author='Ternaris',
    author_email='team@ternaris.com',
    license='CC0-1.0',
    packages=['marv_tutorial'],
    install_requires=[
        'marv',
        'marv-robotics',
        'matplotlib',
        'mpld3',
        'plotly',
    ],
    include_package_data=True,
    zip_safe=False,
)
