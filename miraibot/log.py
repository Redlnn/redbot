import logging
import sys

logger = logging.getLogger("miraibot")
fms="[%(asctime)s] %(levelname)s : %(message)s"
datefmt="%Y-%m-%d %H:%M:%S"

default_handler = logging.StreamHandler(sys.stdout)
default_handler.setFormatter(logging.Formatter(fms, datefmt=datefmt))
logger.addHandler(default_handler)

handler = logging.FileHandler("error.log")
handler.setLevel(logging.ERROR)
handler.setFormatter(logging.Formatter(fms,datefmt=datefmt))
logger.addHandler(handler)

__all__ = [
    "logger"
]
