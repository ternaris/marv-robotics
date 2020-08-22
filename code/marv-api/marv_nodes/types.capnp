# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

@0xd985651e70b6d5e4;

using import "/marv_pycapnp/types.capnp".Timestamp;


struct Dataset {
  id0 @0 :UInt64;
  id1 @1 :UInt64;
  name @2 :Text;
  files @3 :List(File);
  timeAdded @4 :Timestamp;
  timestamp @5 :Timestamp;
}

# TODO:
# - remote files
# - URLs for e.g. git commits

struct File {
  path @0 :Text;
  missing @1 :Bool;
  mtime @2 :Timestamp;
  size @3 :UInt64;
}


struct Comment {
  author @0 :Text;
  text @1 :Text;
  timeAdded @2 :Timestamp;
}


struct GeoJson {
  union {
    feature @0 :Feature;
    featureCollection @1 :FeatureCollection;
    point @2 :Point;
    multiPoint @3 :MultiPoint;
    lineString @4 :LineString;
    multiLineString @5 :MultiLineString;
    polygon @6 :Polygon;
    multiPolygon @7 :MultiPolygon;
    geometryCollection @8 :GeometryCollection;
  }

  struct Geometry {
    union {
      point @0 :Point;
      multiPoint @1 :MultiPoint;
      lineString @2 :LineString;
      multiLineString @3 :MultiLineString;
      geometryCollection @4 :GeometryCollection;
      polygon @5 :Polygon;
      multiPolygon @6 :MultiPolygon;
    }
  }

  using Position = List(Float64);

  struct Feature {
    geometry @0 :Geometry;
    properties @1 :Properties;
  }

  struct FeatureCollection {
    features @0 :List(Feature);
  }

  struct Point {
    coordinates @0 :Position;
  }

  struct MultiPoint {
    coordinates @0 :List(Position);
  }

  struct LineString {
    coordinates @0 :List(Position);
  }

  struct MultiLineString {
    coordinates @0 :List(List(Position));
  }

  struct LinearRing {
    coordinates @0 :List(Position);
  }

  struct Polygon {
    coordinates @0 :List(List(Position));
  }

  struct MultiPolygon {
    coordinates @0 :List(List(List(Position)));
  }

  struct GeometryCollection {
    geometries @0 :List(Geometry);
  }

  struct Properties {
    coordinatesystem @0 :Text = "WGS84";    # `WGS84` or `cartesian
    color @1 :List(Float32);                # global color [rgba]
    colors @2 :List(List(Float32));         # per vertex color [[rgba]]
    fillcolor @3 :List(Float32);            # global fill color [rgba]
    fillcolors @4 :List(List(Float32));     # per vertex fill color [[rgba]]
    width @5 :Float32;                      # linewidth / strokewith of filled geometry
    timestamps @6 :List(UInt64);            # per vertex timestamp used for playback
    rotations @7 :List(Float64);            # per vertex rotations if markers are used
    markervertices @8 :List(Float64);       # rotation marker polygon (e.g. `[0, 0, -1, .3, -1, -.3]`)
  }
}


struct PointCloud {
  vertices @0 :List(List(Float64));
  timestamp @1 :Timestamp;
}


struct Tag {
  text @0 :Text;
}


struct Words {
  words @0 :List(Text);
}
