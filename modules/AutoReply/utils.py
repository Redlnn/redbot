#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BytesIO


async def img_2_bytesio(img_path: str):
    with open(img_path, 'rb') as f:
        content = f.read()
    return BytesIO(content).getvalue()
