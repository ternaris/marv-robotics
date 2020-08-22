# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

@0x8070aafdd912e760;


enum EnumType {
  foo @0;
  bar @1;
}


struct TestStruct {
  text @0 :Text;
  data @1 :Data;
  textList @2 :List(Text);
  dataList @3 :List(Data);
  textListInList @12 :List(List(Text));
  dataListInList @13 :List(List(Data));
  nestedList @4 :List(TestStruct);
  union {
    unionText @5 :Text;
    unionData @6 :Data;
  }
  union :union {
    text @7 :Text;
    data @8 :Data;
  }
  group :group {
    text @9 :Text;
    data @10 :Data;
  }
  enum @11 :EnumType;
}
