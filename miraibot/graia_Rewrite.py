#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import traceback

from graia.broadcast import Broadcast

from .logger import logger


def tracebacks():
    logger.error(traceback.format_exc())


traceback.print_exc = tracebacks


class Broc(Broadcast):
    async def Executor(self, *args, **kwargs):
        await super().Executor(*args, **kwargs)
