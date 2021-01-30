"""
用法:


>>> from os import path

>>> import config
>>> import miraibot

>>> if __name__ == "__main__":
>>>     miraibot.init(config)
>>>     miraibot.load_plugins(
>>>         path.join(path.dirname(__file__), 'plugins'),
>>>         'plugins'
>>>     )
>>>     miraibot.run()
"""

import asyncio
from typing import Any, Optional
import traceback

# from graia.broadcast import Broadcast
from .graia_Rewrite import Broc as Broadcast
from graia.application import GraiaMiraiApplication, Session

from .log import logger
from . import schedule

try:
    import aioredis
    import aioredis.abc
except (ModuleNotFoundError, AttributeError):
    aioredis = None


class miraibot(GraiaMiraiApplication):
    def __init__(self, config_dict: dict, **kwargs):
        super().__init__(
            connect_info=Session(
                host=f"http://{config_dict['HOST']}:{config_dict['PORT']}",  # 填入 httpapi 服务运行的地址 # noqa
                authKey=config_dict['AUTHKEY'],  # 填入 authKey
                account=config_dict['QQ'],  # 你的机器人的 qq 号
                websocket=True  # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
            ),
            **kwargs
        )
        self.logger.debug(f'加载的配置: {config_dict}')

        self.config = config_dict
        # self.asgi.debug = self.config.DEBUG


app: miraibot = None
loop: asyncio.get_event_loop() = None
bcc: Broadcast = None
redis = None


def init(config_object: Optional[Any] = None, **kwargs) -> None:
    """
    初始化 miraibot

    此函数必须在代码的开始处调用
    否则，got_bot() 函数将返回 None 且无法正常工作
    :param config_object: 包含框架所需的配置的对象
    """
    import logging
    global app, loop, bcc, redis

    if config_object is None:
        from . import default_config as config_object

    config_dict = {
        k: v
        for k, v in config_object.__dict__.items()
        if k.isupper() and not k.startswith('_')
    }

    for i in ('HOST', 'PORT', 'AUTHKEY', 'QQ'):
        if i not in config_dict:
            raise ValueError(f'配置文件中缺失 HOST 或 PORT 或 AUTHKEY 或 QQ: {i}')

    if config_dict['DEBUG']:
        logger.setLevel(logging.DEBUG)
        debug = True
    else:
        logger.setLevel(logging.INFO)
        debug = False

    loop = asyncio.get_event_loop()
    bcc = Broadcast(loop=loop, debug_flag=debug)
    loop.create_task(schedule.run_pending())
    app = miraibot(
        config_dict=config_dict,
        logger=logger,
        broadcast=bcc,
        debug=debug,
        **kwargs
    )

    if aioredis is not None and config_dict["REDIS"]:
        redis = asyncio.get_event_loop().run_until_complete(
            aioredis.create_pool(
                f"redis://{config_dict['REDIS_HOST']}:{config_dict['REDIS_PORT']}", # noqa
                db=config_dict["REDIS_DB"], password=config_dict["REDIS_PASSWORD"], # noqa
                minsize=config_dict["REDIS_MINSIZE"], maxsize=config_dict["REDIS_MAXSIZE"], # noqa
                loop = loop # noqa
            )
        )


class get:
    @staticmethod
    def bot() -> miraibot:
        if app is None:
            raise ValueError('miraibot 实例尚未初始化')
        return app

    @staticmethod
    def loop() -> asyncio.get_event_loop:
        if loop is None:
            raise ValueError('loop 实例尚未初始化')
        return loop

    @staticmethod
    def bcc() -> Broadcast:
        if bcc is None:
            raise ValueError('Broadcast 实例尚未初始化')
        return bcc

    @staticmethod
    def redis() -> redis:
        if aioredis is None or redis is None:
            raise ValueError("依赖模块 aioredis 未正确安装或未正确初始化")
        return redis


def run():
    try:
        get.bot().launch_blocking()
    except Exception as e: # noqa
        logger.critical(traceback.format_exc())
    except KeyboardInterrupt:
        for module in get_loaded_plugins():
            module.__end__()
        logger.info("Bye~")


from .plugin import ( # noqa
    load_plugin,
    load_plugins,
    load_builtin_plugins,
    get_loaded_plugins
)

__all__ = [
    "init", "run", "get", "miraibot",
    "GraiaMiraiApplication",
    "load_plugin", "load_plugins", "load_builtin_plugins", "get_loaded_plugins", # noqa
    "schedule", "logger"
]
