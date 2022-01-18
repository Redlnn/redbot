#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
from os.path import abspath, isdir, isfile, join

from graia.ariadne.adapter import DefaultAdapter
from graia.ariadne.app import Ariadne
from graia.ariadne.console import Console
from graia.ariadne.console.saya import ConsoleBehaviour
from graia.ariadne.model import MiraiSession
from graia.broadcast import Broadcast
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler import GraiaScheduler
from graia.scheduler.saya import GraiaSchedulerBehaviour
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from utils.config import get_main_config, get_modules_config
from utils.logger import change_logger
from utils.path import modules_path, root_path

basic_cfg = get_main_config()
modules_cfg = get_modules_config()
ignore = ('__init__.py', '__pycache__')

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    bcc = Broadcast(loop=loop)
    app = Ariadne(
        DefaultAdapter(
            broadcast=bcc,
            mirai_session=MiraiSession(
                host=basic_cfg.miraiApiHttp.host,  # 填入 httpapi 服务运行的地址
                account=basic_cfg.miraiApiHttp.account,  # 你的机器人的 qq 号
                verify_key=basic_cfg.miraiApiHttp.verifyKey,  # 填入 verifyKey
            ),
            log=False,
        ),
        loop=loop,
        chat_log_config=None if basic_cfg.logChat else False,
    )
    console = Console(
        broadcast=bcc,
        prompt=HTML('<split_1></split_1><redbot> redbot </redbot><split_2></split_2> '),
        style=Style(
            [
                ('split_1', 'fg:#61afef'),
                ('redbot', 'bg:#61afef fg:#ffffff'),
                ('split_2', 'fg:#61afef'),
            ]
        ),
        replace_logger=False,
    )
    saya = Saya(bcc)
    saya.install_behaviours(BroadcastBehaviour(bcc))
    saya.install_behaviours(ConsoleBehaviour(console))
    saya.install_behaviours(GraiaSchedulerBehaviour(GraiaScheduler(loop, bcc)))
    console.start()
    change_logger(basic_cfg.debug, True if console else False)  # 对logger进行调整，必须放在这里

    with saya.module_context():
        core_modules_path = abspath(join(root_path, 'core_modules'))
        for module in os.listdir(core_modules_path):
            if module in modules_cfg.globalDisabledModules or module[:-3] in modules_cfg.globalDisabledModules:
                continue
            elif module in ignore or module[0] in ('!', '#', '.'):
                continue
            elif isdir(join(core_modules_path, module)):
                saya.require(f'core_modules.{module}')
            elif isfile(join(core_modules_path, module)) and module[-3:] == '.py':
                saya.require(f'core_modules.{module[:-3]}')

    if modules_cfg.enabled:
        with saya.module_context():
            for module in os.listdir(modules_path):
                if module in modules_cfg.globalDisabledModules or module[:-3] in modules_cfg.globalDisabledModules:
                    continue
                elif module in ignore or module[0] in ('!', '#', '.'):
                    continue
                elif isdir(join(modules_path, module)):
                    saya.require(f'modules.{module}')
                elif isfile(join(modules_path, module)) and module[-3:] == '.py':
                    saya.require(f'modules.{module[:-3]}')

    app.launch_blocking()
    console.stop()
