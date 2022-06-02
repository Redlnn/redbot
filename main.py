#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import pkgutil
from pathlib import Path

from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import (
    HttpClientConfig,
    WebsocketClientConfig,
    config,
)
from graia.ariadne.model import LogConfig
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler import GraiaScheduler
from graia.scheduler.saya import GraiaSchedulerBehaviour

from util import log_level_handler
from util.config import basic_cfg, modules_cfg
from util.database import Database
from util.logger_rewrite import rewrite_ariadne_logger
from util.path import modules_path, root_path
from util.send_action import Safe

if __name__ == '__main__':

    ignore = ('__init__.py', '__pycache__')

    if basic_cfg.miraiApiHttp.account == 123456789:
        raise ValueError('在?¿ 填一下配置文件？')

    loop = asyncio.new_event_loop()

    Ariadne.config(loop=loop, install_log=True)
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
    app.create(GraiaScheduler)
    saya = app.create(Saya)
    saya.install_behaviours(
        app.create(BroadcastBehaviour),
        app.create(GraiaSchedulerBehaviour),
    )

    rewrite_ariadne_logger(basic_cfg.debug)

    with saya.module_context():
        core_modules_path = Path(root_path, 'core_modules')
        for module in pkgutil.iter_modules([str(core_modules_path)]):
            if module.name in ignore or module.name[0] in ('#', '.', '_'):
                continue
            saya.require(f"core_modules.{module.name}")

    if modules_cfg.enabled:
        with saya.module_context():
            for module in pkgutil.iter_modules([str(modules_path)]):
                if module.name in ignore or module.name[0] in ('#', '.', '_'):
                    continue
                saya.require(f"modules.{module.name}")

    loop.run_until_complete(Database.init())

    # if not Path(f"{root_path}", "alembic_data").exists():
    #     from shutil import copyfile

    #     os.system("poetry run alembic init alembic_data")
    #     copyfile(Path(root_path, 'util', 'database', 'env.py'), Path(root_path, 'alembic_data', 'env.py'))
    #     del copyfile
    # os.system("poetry run alembic revision --autogenerate -m 'update'")
    # os.system("poetry run alembic upgrade head")

    Ariadne.launch_blocking()
