#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from graia.amnesia.builtins.starlette import StarletteService
from launart import ExportInterface, Launchable
from loguru import logger

from util import GetAiohttpSession
from util.database import Database


class FastAPIStarletteService(StarletteService):
    def __init__(self, fastapi: FastAPI | None = None) -> None:
        self.fastapi = fastapi or FastAPI()
        self.fastapi.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )
        super().__init__(self.fastapi)


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
