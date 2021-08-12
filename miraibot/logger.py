#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys

from colorlog import ColoredFormatter

logger = logging.getLogger('MiraiBot')
console_fms = "%(log_color)s[%(asctime)s %(name)s %(levelname)s] %(message)s"
file_fms = "[%(asctime)s %(name)s %(levelname)s] %(message)s"
# datefmt = "%Y-%m-%d %H:%M:%S"
date_fmt = "%m-%d %H:%M:%S"

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(ColoredFormatter(console_fms,
                                              datefmt=date_fmt,
                                              reset=True,
                                              log_colors={
                                                  'DEBUG': 'cyan',
                                                  'INFO': 'white',
                                                  'WARNING': 'yellow',
                                                  'ERROR': 'red',
                                                  'CRITICAL': 'red,bg_white'
                                              },
                                              secondary_log_colors={},
                                              style='%'))
logger.addHandler(console_handler)

file_handler = logging.FileHandler('error.log', mode='w+', encoding='utf-8')
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(logging.Formatter(file_fms, datefmt=date_fmt))
logger.addHandler(file_handler)

__all__ = [
    "logger"
]
