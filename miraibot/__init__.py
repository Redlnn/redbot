import asyncio
from typing import Any, Optional, Callable, Awaitable, Dict

from aiohttp import ClientSession
from graia.broadcast import Broadcast
from graia.application import GraiaMiraiApplication, Session

from .logger import LoggingLogger

from . import sched as schedule


class miraibot(GraiaMiraiApplication):
    def __init__(self, config_dict: Dict, **kwargs):
        super().__init__(
            connect_info=Session(
                host=f"http://{config_dict['HOST']}:{config_dict['PORT']}",  # 填入 httpapi 服务运行的地址
                authKey=config_dict['AUTHKEY'],  # 填入 authKey
                account=config_dict['QQ'],  # 你的机器人的 qq 号
                websocket=True  # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
            ),
            **kwargs
        )
        self.logger.debug(f'加载的配置: {config_dict}')

        self.config = config_dict
        # self.asgi.debug = self.config.DEBUG


_app: Optional[miraibot] = None
_loop: Optional[asyncio.get_event_loop] = None
_bcc: Optional[Broadcast] = None


def init(config_object: Optional[Any] = None, **kwargs) -> None:
    """
    初始化 miraibot

    此函数必须在代码的开始处调用
    否则，got_bot() 函数将返回 None 且无法正常工作
    :param config_object: 包含框架所需的配置的对象
    """
    import logging
    global _app, _loop, _bcc

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
        logger = LoggingLogger(level=logging.DEBUG)
        debug = True
    else:
        logger = LoggingLogger(level=logging.INFO)
        debug = False

    _loop = asyncio.get_event_loop()
    _bcc = Broadcast(loop=_loop, debug_flag=debug)
    schedule.init(_loop)
    _app = miraibot(
        config_dict=config_dict,
        logger=logger,
        broadcast=_bcc,
        debug=debug,
        **kwargs
    )


def get_bot() -> miraibot:
    if _app is None:
        raise ValueError('miraibot 实例尚未初始化')
    return _app


def get_loop() -> object:
    if _loop is None:
        raise ValueError('miraibot 实例尚未初始化')
    return _loop


def get_bcc() -> object:
    if _bcc is None:
        raise ValueError('miraibot 实例尚未初始化')
    return _bcc


def get_lbs(obj):
    if obj in ("bot", "loop", "bcc"):
        return getattr(miraibot, obj)
    else:
        raise ValueError("The object does not exist")


def run():
    try:
        get_bot().launch_blocking()
    except KeyboardInterrupt:
        pass


from .plugin import (
    load_plugin,
    load_plugins,
    load_builtin_plugins,
    get_loaded_plugins
)

if __name__ == '__main__':
    from . import default_config as config
    from os import path

    init(config)
    load_plugins(
        path.join(path.dirname(__file__), 'plugins'), 'plugins'
    )
    run()
