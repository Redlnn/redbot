#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import orjson
from pydantic import BaseModel as PyDanticBaseModel


def orjson_dumps(v, *, default, **dumps_kwargs):
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default, **dumps_kwargs).decode()


class BaseModel(PyDanticBaseModel):
    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
