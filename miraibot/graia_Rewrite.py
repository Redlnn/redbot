from graia.broadcast import Broadcast
import traceback
from .log import logger


def tracebacks():
    logger.error(traceback.format_exc())


traceback.print_exc = tracebacks


class Broc(Broadcast):
    async def Executor(self, *args, **kwargs):
        await super().Executor(*args, **kwargs)
