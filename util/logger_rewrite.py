#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys
from pathlib import Path

from loguru import logger
from prompt_toolkit.patch_stdout import StdoutProxy

from util.path import logs_path


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
        while frame.f_code.co_filename == logging.__file__:  # type: ignore
            frame = frame.f_back  # type: ignore
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, self.format(record))  # 此处与原链接不同


def rewrite_logging_logger(logger_name: str):
    logging_logger = logging.getLogger(logger_name)
    for handler in logging_logger.handlers:
        logging_logger.removeHandler(handler)
    logging_logger.addHandler(InterceptHandler())
    logging_logger.setLevel(logging.DEBUG)


def rewrite_ariadne_logger(debug: bool = False):
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
    logger.add(sys.stderr, level=log_level, format=log_format, backtrace=True, diagnose=True, enqueue=True)
    logger.add(
        Path(logs_path, 'latest.log'),
        rotation='00:00',
        retention="30 days",
        compression='zip',
        encoding='utf-8',
        level=log_level,
        format=log_format,
        colorize=False,
        backtrace=True,  # 格式化的异常跟踪是否应该向上扩展，超出捕获点，以显示生成错误的完整堆栈跟踪。
        diagnose=True,  # 异常跟踪是否应显示变量值以简化调试。这应该在生产中设置为 False 以避免泄露敏感数据。
        enqueue=True,  # 要记录的消息是否应在到达接收器之前首先通过多进程安全队列。这在通过多个进程记录到文件时很有用。这也具有使日志记录调用非阻塞的优点。
    )
