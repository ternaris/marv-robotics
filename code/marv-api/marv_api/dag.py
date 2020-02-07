# Copyright 2020  Ternaris.
# SPDX-License-Identifier: AGPL-3.0-only

# pylint: disable=too-few-public-methods,invalid-name,no-self-argument,no-self-use

from typing import Optional, Union

from pydantic import (
    BaseModel as _BaseModel,
    Extra,
    create_model,
    validator,
)


class BaseModel(_BaseModel):
    class Config:
        extra: Extra.forbid


class Inputs(BaseModel):
    """Base class for node input configuration models.

    The fields of its subclasses describe the input parameters to be
    passed to a node function.
    """

    @classmethod
    def subclass(cls, __module__, **kw):
        return create_model('Inputs', __base__=Inputs, __module__=__module__, **kw)


class Node(BaseModel):  # pylint: disable=too-few-public-methods
    function: str
    inputs: Optional[Inputs]
    message_schema: Optional[str]
    group: Union[bool, str, None]
    version: Optional[int]
    foreach: Optional[str]

    @validator('function')
    def function_needs_to_be_dotted_path(cls, value):
        if '.' not in value:
            raise ValueError(f'Expected dotted path to function, not: {value!r}')
        return value

    def clone(self, **kw):
        return self.copy(update={'inputs': self.inputs.copy(update=kw)})


class Stream(BaseModel):
    node: Node
    name: Optional[str]
