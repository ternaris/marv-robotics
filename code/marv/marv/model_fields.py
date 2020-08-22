# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from tortoise.fields import CharField

from marv_api.setid import SetID


class SetIDField(CharField):
    def __init__(self, max_length=32, **kwargs):
        super().__init__(max_length, **kwargs)

    def to_db_value(self, value: SetID, _) -> str:
        return str(value)

    def to_python_value(self, value: str) -> SetID:
        return SetID(value)
