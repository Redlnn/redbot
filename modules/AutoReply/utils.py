#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BytesIO

from aiofile import async_open


async def img_2_bytes(img_path: str):
    async with async_open(img_path, 'rb') as afp:
        content = await afp.read()
    return BytesIO(content).getvalue()
