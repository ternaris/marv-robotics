# Copyright 2016 - 2018  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=invalid-name

import struct
from base64 import b32decode, b32encode
from random import getrandbits


def decode_setid(encoded):
    """Decode setid as uint128."""
    try:
        lo, hi = struct.unpack('<QQ', b32decode(encoded.upper() + '======'))
    except struct.error:
        raise ValueError(f'Cannot decode {encoded!r}')
    return (hi << 64) + lo


def encode_setid(uint128):
    """Encode uint128 setid as stripped b32encoded string."""
    hi, lo = divmod(uint128, 2**64)
    return b32encode(struct.pack('<QQ', lo, hi))[:-6].decode('ascii').lower()


class SetID(int):
    def __new__(cls, value, hi=None):
        if hi is not None:
            value = (hi << 64) + value
        value = decode_setid(value) if isinstance(value, str) else value
        return super(SetID, cls).__new__(cls, value)

    @classmethod
    def random(cls):
        return cls(getrandbits(128))

    @property
    def hi(self):
        return int(self) // 2**64

    @property
    def lo(self):
        return int(self) % 2**64

    @property
    def lohi(self):
        return tuple(int(x) for x in reversed(divmod(self, 2**64)))

    @property
    def abbrev(self):
        return str(self)[:10]

    def __repr__(self):
        return f"SetID('{str(self)}')"

    def __str__(self):
        return encode_setid(self)
