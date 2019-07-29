# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import os

from . import _monkeypatches

os.environ.setdefault('MATPLOTLIBRC', os.path.dirname(__file__))
