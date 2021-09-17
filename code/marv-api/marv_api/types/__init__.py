# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import capnp  # noqa: F401,TC002  pylint: disable=unused-import

# pylint: disable=no-name-in-module
from marv_detail.types_capnp import Section, Widget
from marv_nodes.types_capnp import Dataset, File, GeoJson, Words
from marv_pycapnp.types_capnp import (
    BoolValue,
    DataValue,
    Float32Value,
    Float64Value,
    Int8Value,
    Int16Value,
    Int32Value,
    Int64Value,
    TextValue,
    TimedBool,
    TimedData,
    TimedFloat32,
    TimedFloat64,
    TimedInt8,
    TimedInt16,
    TimedInt32,
    TimedInt64,
    TimedText,
    TimedUInt8,
    TimedUInt16,
    TimedUInt32,
    TimedUInt64,
    TimelineEvent,
    Timeslice,
    UInt8Value,
    UInt16Value,
    UInt32Value,
    UInt64Value,
)

# pylint: enable=no-name-in-module

__all__ = (
    'BoolValue',
    'Dataset',
    'DataValue',
    'File',
    'Float32Value',
    'Float64Value',
    'GeoJson',
    'Int16Value',
    'Int32Value',
    'Int64Value',
    'Int8Value',
    'Section',
    'TextValue',
    'TimedBool',
    'TimedData',
    'TimedFloat32',
    'TimedFloat64',
    'TimedInt16',
    'TimedInt32',
    'TimedInt64',
    'TimedInt8',
    'TimedText',
    'TimedUInt16',
    'TimedUInt32',
    'TimedUInt64',
    'TimedUInt8',
    'TimelineEvent',
    'Timeslice',
    'UInt16Value',
    'UInt32Value',
    'UInt64Value',
    'UInt8Value',
    'Widget',
    'Words',
)
