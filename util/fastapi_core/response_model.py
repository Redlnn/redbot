#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from util.better_pydantic import BaseModel


class GeneralResponse(BaseModel):
    code: int = 200
    data: dict = {}
    message: str = 'success'
