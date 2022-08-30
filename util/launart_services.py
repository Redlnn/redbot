#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Literal

from launart import ExportInterface, Launchable
from loguru import logger

from util import GetAiohttpSession
from util.database import Database


class DatabeseService(Launchable):
    id: str = 'database/init'

    @property
    def required(self) -> set[str | type[ExportInterface]]:
        return set()

    @property
    def stages(self) -> set[Literal['preparing', 'blocking', 'cleanup']]:
        return set()

    async def launch(self, _):
        logger.info('Initializing database...')
        await Database.init()


class CloseAiohttpSessionService(Launchable):
    id: str = 'close_aiohttp_session'

    @property
    def required(self) -> set[str | type[ExportInterface]]:
        return set()

    @property
    def stages(self) -> set[Literal['preparing', 'blocking', 'cleanup']]:
        return {'cleanup'}

    async def launch(self, _):
        async with self.stage('cleanup'):
            print('Closing aiohttp session...')
            await GetAiohttpSession.close_session()
