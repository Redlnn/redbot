import logging
import sys

logger = logging.getLogger()
default_handler = logging.StreamHandler(sys.stdout)
default_handler.setFormatter(
    logging.Formatter('[%(asctime)s] %(levelname)s :  %(message)s', datefmt="%Y-%m-%d %H:%M:%S"))
logger.addHandler(default_handler)

__all__ = [
    'logger',
]
