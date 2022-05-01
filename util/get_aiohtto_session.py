#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import aiohttp
from aiohttp import ClientSession
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter


def get_session() -> ClientSession:
    session = get_running(Adapter).session
    if session is None:
        session = aiohttp.ClientSession()
    return session
