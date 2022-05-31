#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import aiohttp
from aiohttp import ClientSession


class GetAiohttpSession:
    session: ClientSession

    @classmethod
    def get_session(cls) -> ClientSession:
        if cls.session is None:
            cls.session = aiohttp.ClientSession()
        return cls.session
