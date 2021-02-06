# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

import marv_api.types
from marv_api import deprecation

DEPRECATIONS = {
    name: deprecation.Info(
        __name__, '21.04', getattr(marv_api.types, name),
        f'use marv_api.types.{name} instead.',
    ) for name in (
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
}

__getattr__ = deprecation.make_getattr(__name__, DEPRECATIONS)
