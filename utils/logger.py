#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys
from pathlib import Path

from loguru import logger

from config import config_data

__all__ = ['logger']


# https://loguru.readthedocs.io/en/stable/overview.html?highlight=InterceptHandler#entirely-compatible-with-standard-logging
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


logger.remove()

if config_data['Basic']['Debug']:
    LOG_FORMAT = (
        '<green>{time:YYYY-MM-DD HH:mm:ss.SSSS}</green> | <level>{level: <9}</level> | '
        '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> '
    )
    LOG_LEVEL = 'DEBUG'
else:
    LOG_FORMAT = (
        '<green>{time:YYYY-MM-DD HH:mm:ss.SS}</green> | <level>{level: <8}</level> | '
        '<cyan>{name}</cyan> - <level>{message}</level>'
    )
    LOG_LEVEL = 'INFO'
logger.add(
    Path(Path.cwd(), 'logs', 'latest.log'),
    encoding='utf-8',
    format=LOG_FORMAT,
    rotation='00:00',
    retention="30 days",
    compression='zip',
    backtrace=True,
    diagnose=True,
    colorize=False,
    level=LOG_LEVEL,
)
logger.add(sys.stderr, format=LOG_FORMAT, backtrace=True, diagnose=True, colorize=True, level=LOG_LEVEL)

peewee_logger = logging.getLogger('peewee')
peewee_logger.addHandler(InterceptHandler())
peewee_logger.setLevel(logging.DEBUG)
