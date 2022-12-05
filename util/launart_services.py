from typing import Literal

from launart import ExportInterface, Launchable
from loguru import logger

from util.database import Database


class DatabaseInitService(Launchable):
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
