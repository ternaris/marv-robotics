# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

@0xb7826c391b2ebc91;

using import "/marv_pycapnp/types.capnp".Timedelta;
using import "/marv_pycapnp/types.capnp".Timestamp;

struct Bagmeta {
  bags @0 :List(Bag);
  startTime @1 :Timestamp;
  endTime @2 :Timestamp;
  duration @3 :Timedelta;
  msgCount @4 :UInt64;
  msgTypes @5 :List(Text);
  topics @6 :List(Text);
  connections @7 :List(Connection);
}

struct Bag {
  version @0 :UInt16;
  startTime @1 :UInt64;
  endTime @2 :UInt64;
  duration @3 :UInt64;
  msgCount @4 :UInt64;
  connections @5 :List(Connection);
}

struct Connection {
  topic @0 :Text;
  datatype @1 :Text;
  md5sum @2 :Text;
  msgDef @3 :Text;
  msgCount @4 :UInt64;
  latching @5 :Bool;
  serializationFormat @6 :Text;
}

struct MsgType {
  name @0 :Text;
  md5sum @1 :Text;
  msgDef @2 :Text;
}

struct Topic {
  name @0 :Text;
  msgCount @1 :UInt64;
  msgType @2 :Text;
  msgTypeDef @4: Text;
  msgTypeMd5sum @5: Text;
  latching @3 :Bool;
}

struct Message {
  tidx @0 :UInt32;
  # Message belongs to topic with tidx within header.topics list

  data @1 :Data;
  # Serialized message data

  timestamp @2 :Timestamp;
}
