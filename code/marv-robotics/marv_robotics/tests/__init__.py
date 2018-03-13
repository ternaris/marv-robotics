# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import os
from importlib import import_module

import marv_robotics


for mod in (x for x in os.listdir(os.path.dirname(marv_robotics.__file__))
            if x.endswith('.py')):
    mod = '.' + mod[:-3]
    import_module(mod, 'marv_robotics')
