# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import capnp  # pylint: disable=unused-import

# pylint: disable=no-name-in-module
from marv_detail.types_capnp import Section, Widget
from marv_nodes.types_capnp import Dataset, File, GeoJson, Words
from marv_pycapnp.types_capnp import BoolValue, DataValue, TextValue
from marv_pycapnp.types_capnp import Float32Value, Float64Value
from marv_pycapnp.types_capnp import Int16Value, Int32Value, Int64Value, Int8Value
from marv_pycapnp.types_capnp import TimedBool, TimedData, TimedText
from marv_pycapnp.types_capnp import TimedFloat32, TimedFloat64
from marv_pycapnp.types_capnp import TimedInt16, TimedInt32, TimedInt64, TimedInt8
from marv_pycapnp.types_capnp import TimedUInt16, TimedUInt32, TimedUInt64, TimedUInt8
from marv_pycapnp.types_capnp import UInt16Value, UInt32Value, UInt64Value, UInt8Value
# pylint: enable=no-name-in-module

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
