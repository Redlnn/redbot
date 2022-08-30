#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pkgutil
from asyncio import AbstractEventLoop
from pathlib import Path

from creart import create
from graia.amnesia.builtins.uvicorn import UvicornService
from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import (
    HttpClientConfig,
    WebsocketClientConfig,
    config,
)
from graia.ariadne.model import LogConfig
from graia.saya import Saya

from util import log_level_handler, replace_logger
from util.browser import ChromiumBrowserService
from util.config import basic_cfg, modules_cfg
from util.fastapi_service import FastAPIStarletteService
from util.launart_services import CloseAiohttpSessionService, DatabeseService
from util.path import modules_path, root_path
from util.send_action import Safe

if __name__ == '__main__':

    ignore = ('__init__.py', '__pycache__')

    if basic_cfg.miraiApiHttp.account == 123456789:
        raise ValueError('在?¿ 填一下配置文件？')

    # loop = create(AbstractEventLoop)  # 若不需要 loop.run_until_complete()，则不需要此行
    # 若 create Saya 则可以省掉 bcc 和 scheduler 的
    # sche = create(GraiaScheduler)
    # bcc = create(Broadcast)
    saya = create(Saya)

    Ariadne.options['installed_log'] = True
    app = Ariadne(
        connection=config(
            basic_cfg.miraiApiHttp.account,  # 你的机器人的 qq 号
            basic_cfg.miraiApiHttp.verifyKey,  # 填入 verifyKey
            HttpClientConfig(host=basic_cfg.miraiApiHttp.host),
            WebsocketClientConfig(host=basic_cfg.miraiApiHttp.host),
        ),
        log_config=LogConfig(log_level_handler),
    )
    app.default_send_action = Safe

    app.launch_manager.add_service(DatabeseService())
    app.launch_manager.add_service(FastAPIStarletteService())
    # app.launch_manager.add_service(UvicornService())
    app.launch_manager.add_service(CloseAiohttpSessionService())
    app.launch_manager.add_service(ChromiumBrowserService())

    replace_logger(level=0 if basic_cfg.debug else 20, richuru=True)

    with saya.module_context():
        core_modules_path = Path(root_path, 'core_modules')
        for module in pkgutil.iter_modules([str(core_modules_path)]):
            if module.name in ignore or module.name[0] in ('#', '.', '_'):
                continue
            saya.require(f'core_modules.{module.name}')

    if modules_cfg.enabled:
        with saya.module_context():
            for module in pkgutil.iter_modules([str(modules_path)]):
                if module.name in ignore or module.name[0] in ('#', '.', '_'):
                    continue
                saya.require(f'modules.{module.name}')

    Ariadne.launch_blocking()
