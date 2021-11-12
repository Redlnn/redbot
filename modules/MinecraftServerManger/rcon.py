#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

from loguru import logger
from mctools import RCONClient

from config import config_data

config_data = config_data['Modules']['MinecraftServerManager']['Rcon']

__all__ = ["execute_command"]

__HOST = config_data['Host']  # Hostname of the Minecraft server
__PORT = config_data['Port']  # Port number of the RCON server
__PASSWORD = config_data['Password']  # Password of the RCON server


def execute_command(command: str) -> Optional[str]:
    """

    通过 RCON 连接服务器
    可用于执行控制台指令

    :param command: 需要执行的命令
    :return: 执行命令返回值
    """
    logger.info(f'在服务器【{__HOST}:{__PORT}】上执行命令【{command}】')
    rcon = RCONClient(host=__HOST, port=__PORT, format_method=2, timeout=6)
    try:
        rcon.login(__PASSWORD)
    except Exception as e:
        logger.error(f'通过RCON连接【{__HOST}:{__PORT}】失败')
        logger.exception(e)
        raise e
    resp: str = rcon.command(command)
    if resp == '':
        return None
    else:
        return resp
