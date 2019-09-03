# Copyright 2016 - 2019  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

from tortoise.fields import TextField

from marv_node.setid import SetID


class SetIDField(TextField):
    def to_db_value(self, value: SetID, _) -> str:
        return str(value)

    def to_python_value(self, value: str) -> SetID:
        return SetID(value)
