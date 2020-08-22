# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import os
from importlib import import_module

import marv_robotics

for mod in (x for x in os.listdir(os.path.dirname(marv_robotics.__file__))
            if x.endswith('.py')):
    mod = '.' + mod[:-3]
    import_module(mod, 'marv_robotics')
