import aiomcrcon
from aiomcrcon import Client
from loguru import logger

from .config import config


async def execute_command(command: str) -> str:
    """
    通过 RCON 连接服务器
    可用于执行控制台指令

    :param command: 需要执行的命令
    :return: 执行命令返回值
    """
    logger.info(f'在服务器【{config.rcon.host}:{config.rcon.port}】上执行命令【{command}】')
    try:
        async with Client(config.rcon.host, config.rcon.port, config.rcon.passwd) as client:
            resp = await client.send_cmd(command)
    except aiomcrcon.RCONConnectionError as e:
        logger.error(f'通过RCON连接【{config.rcon.host}:{config.rcon.port}】失败')
        raise ValueError(f'通过RCON连接【{config.rcon.host}:{config.rcon.port}】失败') from e
    except aiomcrcon.IncorrectPasswordError as e:
        logger.error(f'通过RCON连接【{config.rcon.host}:{config.rcon.port}】失败，密码错误')
        raise ValueError(f'通过RCON连接【{config.rcon.host}:{config.rcon.port}】失败，密码错误') from e
    else:
        return resp[0]
