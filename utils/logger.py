#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys
from pathlib import Path

from loguru import logger

__all__ = ['change_logger']


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


def change_logger(debug: bool = False):
    logger.remove()
    if debug:
        log_format = (
            '<green>{time:YYYY-MM-DD HH:mm:ss.SSSS}</green> | <level>{level: <9}</level> | '
            '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> '
        )
        log_level = 'DEBUG'
    else:
        log_format = (
            '<green>{time:YYYY-MM-DD HH:mm:ss.SS}</green> | <level>{level: <8}</level> | '
            '<cyan>{name}</cyan> - <level>{message}</level>'
        )
        log_level = 'INFO'
    logger.add(
        Path(Path.cwd(), 'logs', 'latest.log'),
        encoding='utf-8',
        format=log_format,
        rotation='00:00',
        retention="30 days",
        compression='zip',
        backtrace=True,
        diagnose=True,
        colorize=False,
        level=log_level,
    )
    logger.add(sys.stderr, format=log_format, backtrace=True, diagnose=True, colorize=True, level=log_level)

    peewee_logger = logging.getLogger('peewee')
    peewee_logger.addHandler(InterceptHandler())
    peewee_logger.setLevel(logging.DEBUG)

    return logger
