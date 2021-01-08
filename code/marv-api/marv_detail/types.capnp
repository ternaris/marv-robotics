# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

@0xa1475499038e2711;

using import "/marv_nodes/types.capnp".Comment;
using import "/marv_nodes/types.capnp".File;
using import "/marv_nodes/types.capnp".GeoJson;
using import "/marv_pycapnp/types.capnp".Timedelta;
using import "/marv_pycapnp/types.capnp".Timestamp;
using import "/marv_pycapnp/types.capnp".TimelineEvent;

using Filesize = UInt64;
using RowId = UInt64;


enum Align {
  left @0;
  center @1;
  right @2;
}


enum Formatter {
  string @0;
  filesize @1;
  int @2;
  rellink @3;
  datetime @4;
  timedelta @5;
  link @6;
  route @7;
  distance @8;
  speed @9;
  acceleration @10;
}


struct Cell {
  union {
    void @0 :Void;
    text @1 :Text;
    bool @2 :Bool;
    uint64 @3 :UInt64;
    link @4 :Link;
    timedelta @5 :Timedelta;
    timestamp @6 :Timestamp;
    route @7 :Route;
  }
}


struct Link {
  href @0 :Text;
  target @1 :Text = "_blank";
  title @2 :Text;
  download @3 :Text;
}


struct Route {
  route @0 :Text;
  id @1 :Text;
  title @2 :Text;
}


struct Compare {
  sections @0 :List(Section);
  title @1 :Text;
  error @2 :Text;
}


struct Detail {
  sections @0 :List(Section);
  summary @1 :Section;
  title @2 :Text;
  error @3 :Text;
}


struct Section {
  title @0 :Text;
  widgets @1 :List(Widget);
}


struct Widget {
  title @0 :Text;
  union {
    void @1 :Void;
    custom @12 :Custom;
    dropdown @14 :Dropdown;
    gallery @2 :Gallery;
    image @3 :Image;
    keyval @4 :Keyval;
    link @13 :Link;
    mpld3 @5 :Text;  # marv-partial or json
    map @6 :Map;
    mapPartial @11 :Text;
    pre @7 :Pre;
    table @8 :Table;
    pointcloud @9 :Pointcloud;
    video @10 :Video;
    plotly @15: Text;  # marv-partial
    pdf @16 :Pdf;  # marv-partial
    eventlist @17 :Eventlist;
  }

  struct Custom {
    type @0 :Text;
    data @1 :Text;  # json
  }

  struct Gallery {
    images @0 :List(Image);
  }

  struct Image {
    src @0 :Text;
  }

  struct Keyval {
    items @0 :List(Item);

    struct Item {
      title @0 :Text;
      formatter @1 :Formatter;
      list @2 :Bool;
      cell @3 :Cell;
    }
  }

  struct Map {
    zoom @0 :Zoom;
    layers @1 :List(Layer);
    bgcolor @2 :List(UInt8) = [240, 240, 240, 255];  # rgba
    speed :group {
      min @3 :Float32 = 1.0;
      max @4 :Float32 = 1000.0;
      default @5 :Float32 = 1.0;
    }

    struct Layer {
      title @0 :Text;
      color @1 :List(UInt8);
      transform @2 :List(Float32) = [1, 0, 0, 0,
                                     0, 1, 0, 0,
                                     0, 0, 1, 0,
                                     0, 0, 0, 1];
      union {
        geojson @3 :GeoJson;
        tiles @4 :List(Tile);
      }
    }

    struct Tile {
      title @0 :Text;
      url @1 :Text;
      attribution @2: Text;
      zoom @3 :Zoom;
      retina @4 :UInt8 = 1;
    }

    struct Zoom {
      min @0 :Int8;
      max @1 :Int8;
    }
  }

  struct Dropdown {
    widgets @0 :List(Widget);
  }

  struct Pre {
    text @0 :Text;
  }

  struct Table {
    actions @0 :List(Action);
    columns @1 :List(Column);
    rows @2 :List(Row);
    sortcolumn @3 :Int16;
    sortorder @4 :Sortorder;

    struct Action {
      name @0 :Text;
      title @1 :Text;
      method @2 :HTTPMethod;
      data @3 :Text;

      enum HTTPMethod {
        post @0;
        get @1;
      }
    }

    struct Column {
      title @0 :Text;
      align @1 :Align;
      formatter @2 :Formatter;
      list @3 :Bool;
      sortkey @4 :Text;
    }

    struct Row {
      id @0 :RowId;
      cells @1 :List(Cell);
    }

    enum Sortorder {
      ascending @0;
      descending @1;
    }
  }

  struct Pointcloud {
    uri @0 :Text;
    # TODO: rename to blob or stream or src like for image and video?
    size @1 :UInt64;
    # Bytesize of point cloud stream blob
    pointsize @2 :Float32;
    transform @3 :List(Float32) = [1, 0, 0, 0,
                                   0, 1, 0, 0,
                                   0, 0, 1, 0,
                                   0, 0, 0, 1];
    speed :group {
      min @4 :Float32 = 1.0;
      max @5 :Float32 = 1000.0;
      default @6 :Float32 = 1.0;
    }
    rangex @7 :List(Float32);
    rangey @8 :List(Float32);
    rangez @9 :List(Float32);
    ranged @10 :List(Float32);
    frameid @11 :Text;
  }

  struct Video {
    src @0 :Text;
  }

  struct Pdf {
    src @0 :Text;
  }

  struct Eventlist {
    subtype @0: Text;
    events @1 :List(TimelineEvent);
  }
}
