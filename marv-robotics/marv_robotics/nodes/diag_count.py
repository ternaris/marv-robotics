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

from collections import defaultdict

import marv
from diagnostic_msgs.msg import DiagnosticStatus


LEVELS = {getattr(DiagnosticStatus, x): x for x in ['OK', 'WARN', 'ERROR', 'STALE']}


@marv.node()
@marv.input('messages', filter=['/diagnostics:diagnostic_msgs/DiagnosticArray'])
def diag_count(messages):
    counters = defaultdict(lambda: defaultdict(int))
    for stat in (stat for _, msg, _ in messages for stat in msg.status):
        counters[stat.name][LEVELS[stat.level]] += 1
    counters = {k: dict(v, name=k) for k, v in counters.items()}
    return counters
