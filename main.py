#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pkgutil
from os.path import abspath, join

from graia.ariadne.app import Ariadne
from graia.ariadne.console import Console
from graia.ariadne.console.saya import ConsoleBehaviour
from graia.ariadne.model import MiraiSession
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler import GraiaScheduler
from graia.scheduler.saya import GraiaSchedulerBehaviour
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from util.config import get_basic_config, get_modules_config
from util.logger_rewrite import rewrite_ariadne_logger, rewrite_logging_logger
from util.path import modules_path, root_path
from util.send_action import Safe

basic_cfg = get_basic_config()
modules_cfg = get_modules_config()
ignore = ('__init__.py', '__pycache__')

if __name__ == '__main__':
    app = Ariadne(
        MiraiSession(
            host=basic_cfg.miraiApiHttp.host,  # 填入 httpapi 服务运行的地址
            account=basic_cfg.miraiApiHttp.account,  # 你的机器人的 qq 号
            verify_key=basic_cfg.miraiApiHttp.verifyKey,  # 填入 verifyKey
        ),
        chat_log_config=None if basic_cfg.logChat else False,
    )
    app.adapter.log = False
    app.default_send_action = Safe
    loop = app.loop
    bcc = app.broadcast
    saya = Saya(bcc)
    saya.install_behaviours(
        BroadcastBehaviour(bcc),
        GraiaSchedulerBehaviour(app.create(GraiaScheduler)),
    )
    if basic_cfg.console:
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
        saya.install_behaviours(ConsoleBehaviour(console))
    else:
        console = None

    rewrite_ariadne_logger(basic_cfg.debug, True if console else False)  # 对logger进行调整，必须放在这里
    rewrite_logging_logger('peewee')

    with saya.module_context():
        core_modules_path = abspath(join(root_path, 'core_modules'))
        for module in pkgutil.iter_modules([core_modules_path]):
            if (
                module.name in modules_cfg.globalDisabledModules
                or module.name[:-3] in modules_cfg.globalDisabledModules
            ):
                continue
            elif module.name in ignore or module.name[0] in ('!', '#', '.'):
                continue
            elif module.name == 'console' and not basic_cfg.console:
                continue
            saya.require(f"core_modules.{module.name}")

    if modules_cfg.enabled:
        with saya.module_context():
            for module in pkgutil.iter_modules([modules_path]):
                if (
                    module.name in modules_cfg.globalDisabledModules
                    or module.name[:-3] in modules_cfg.globalDisabledModules
                ):
                    continue
                elif module.name in ignore or module.name[0] in ('!', '#', '.', '_'):
                    continue
                saya.require(f"modules.{module.name}")

    app.launch_blocking()
