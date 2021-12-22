#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from loguru import logger
from mctools import RCONClient

from .config import config

__all__ = ['execute_command']


def execute_command(command: str) -> str:
    """
    通过 RCON 连接服务器
    可用于执行控制台指令

    :param command: 需要执行的命令
    :return: 执行命令返回值
    """
    logger.info(f'在服务器【{config.rcon.host}:{config.rcon.port}】上执行命令【{command}】')
    rcon = RCONClient(host=config.rcon.host, port=config.rcon.port, format_method=2, timeout=6)
    try:
        rcon.login(config.rcon.passwd)
    except Exception as e:
        logger.error(f'通过RCON连接【{config.rcon.host}:{config.rcon.port}】失败')
        logger.exception(e)
        raise e
    resp: str = rcon.command(command)
    return resp
