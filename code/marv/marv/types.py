# -*- coding: utf-8 -*-
#
# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import absolute_import, division, print_function

import capnp

from marv_detail.types_capnp import Section, Widget
from marv_nodes.types_capnp import Dataset, File, GeoJson, Words
from marv_pycapnp.types_capnp import BoolValue, TextValue, DataValue
from marv_pycapnp.types_capnp import Float32Value, Float64Value
from marv_pycapnp.types_capnp import Int8Value, Int16Value, Int32Value, Int64Value
from marv_pycapnp.types_capnp import UInt8Value, UInt16Value, UInt32Value, UInt64Value
from marv_pycapnp.types_capnp import TimedBool, TimedText, TimedData
from marv_pycapnp.types_capnp import TimedFloat32, TimedFloat64
from marv_pycapnp.types_capnp import TimedInt8, TimedInt16, TimedInt32, TimedInt64
from marv_pycapnp.types_capnp import TimedUInt8, TimedUInt16, TimedUInt32, TimedUInt64

__all__ = (
    'Section', 'Widget',
    'Dataset', 'File', 'GeoJson', 'Words',
    'BoolValue', 'TextValue', 'DataValue',
    'Float32Value', 'Float64Value',
    'Int8Value', 'Int16Value', 'Int32Value', 'Int64Value',
    'UInt8Value', 'UInt16Value', 'UInt32Value', 'UInt64Value',
    'TimedBool', 'TimedText', 'TimedData',
    'TimedFloat32', 'TimedFloat64',
    'TimedInt8', 'TimedInt16', 'TimedInt32', 'TimedInt64',
    'TimedUInt8', 'TimedUInt16', 'TimedUInt32', 'TimedUInt64',
)

