#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import sys

from colorlog import ColoredFormatter
from logging import shutdown as log_shutdown

logger = logging.getLogger('MiraiBot')
console_fms = "%(log_color)s[%(asctime)s %(name)s %(levelname)s] %(message)s"
file_fms = "[%(asctime)s %(name)s %(levelname)s] %(message)s"
# datefmt = "%Y-%m-%d %H:%M:%S"
date_fmt = "%m-%d %H:%M:%S"

log_file_path = os.path.join('error.log')

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

file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(logging.Formatter(file_fms, datefmt=date_fmt))
logger.addHandler(file_handler)


def stop_log_and_del_empty_log():
    log_shutdown()
    if os.path.getsize(log_file_path) == 0:
        os.remove(log_file_path)


__all__ = [
    logger, stop_log_and_del_empty_log
]
