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
from importlib import import_module

from marv_robotics import nodes


for mod in (x for x in os.listdir(os.path.dirname(nodes.__file__))
            if x.endswith('.py')):
    mod = '.' + mod[:-3]
    import_module(mod, 'marv_robotics.nodes')
