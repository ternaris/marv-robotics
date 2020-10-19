# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

@0x8ce54f16698f41e9;

using Timedelta = UInt64;
using Timestamp = UInt64;

struct BoolValue {
  value @0 :Bool;
}

struct Int8Value {
  value @0 :Int8;
}

struct Int16Value {
  value @0 :Int16;
}

struct Int32Value {
  value @0 :Int32;
}

struct Int64Value {
  value @0 :Int64;
}

struct UInt8Value {
  value @0 :UInt8;
}

struct UInt16Value {
  value @0 :UInt16;
}

struct UInt32Value {
  value @0 :UInt32;
}

struct UInt64Value {
  value @0 :UInt64;
}

struct Float32Value {
  value @0 :Float32;
}

struct Float64Value {
  value @0 :Float64;
}

struct TextValue {
  value @0 :Text;
}

struct DataValue {
  value @0 :Data;
}

struct TimedBool {
  value @0 :Bool;
  timestamp @1 :Timestamp;
}

struct TimedInt8 {
  value @0 :Int8;
  timestamp @1 :Timestamp;
}

struct TimedInt16 {
  value @0 :Int16;
  timestamp @1 :Timestamp;
}

struct TimedInt32 {
  value @0 :Int32;
  timestamp @1 :Timestamp;
}

struct TimedInt64 {
  value @0 :Int64;
  timestamp @1 :Timestamp;
}

struct TimedUInt8 {
  value @0 :UInt8;
  timestamp @1 :Timestamp;
}

struct TimedUInt16 {
  value @0 :UInt16;
  timestamp @1 :Timestamp;
}

struct TimedUInt32 {
  value @0 :UInt32;
  timestamp @1 :Timestamp;
}

struct TimedUInt64 {
  value @0 :UInt64;
  timestamp @1 :Timestamp;
}

struct TimedFloat32 {
  value @0 :Float32;
  timestamp @1 :Timestamp;
}

struct TimedFloat64 {
  value @0 :Float64;
  timestamp @1 :Timestamp;
}

struct TimedText {
  value @0 :Text;
  timestamp @1 :Timestamp;
}

struct TimedData {
  value @0 :Data;
  timestamp @1 :Timestamp;
}

struct Timeslice {
  start @0 :Timestamp;
  # Start of slice
  stop @1 :Timestamp;
  # End of slice (exclusive)
}

struct TimelineEvent {
  time @0 :Timestamp;
  type @1 :Text;
  payload @2 :Text;
}


# Below here unused so far

struct Datetime {
  timestamp @0 :Timestamp;
  # ns since epoch

  tzoffset @1 :Int16;
  # timezone offset in minutes
}

struct Map(Key, Value) {
  items @0 :List(Item);

  struct Item {
    key @0 :Key;
    value @1 :Value;
  }
}
