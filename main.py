#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from datetime import datetime
from pathlib import Path

from graia.ariadne.app import Ariadne
from graia.ariadne.console import Console
from graia.ariadne.console.saya import ConsoleBehaviour
from graia.ariadne.model import MiraiSession
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler import GraiaScheduler
from graia.scheduler.saya import GraiaSchedulerBehaviour

from utils.config import get_main_config, get_modules_config
from utils.logger import change_logger
from utils.path import modules_path

basic_cfg = get_main_config()
modules_cfg = get_modules_config()

if __name__ == '__main__':
    app = Ariadne(
        MiraiSession(
            host=basic_cfg.miraiApiHttp.host,  # 填入 httpapi 服务运行的地址
            account=basic_cfg.miraiApiHttp.account,  # 你的机器人的 qq 号
            verify_key=basic_cfg.miraiApiHttp.verifyKey,  # 填入 verifyKey
        ),
        chat_log_config=None if basic_cfg.logChat else False,
    )
    console = Console(
        broadcast=app.broadcast,
        r_prompt="<{current_time}>",
        style={
            "rprompt": "bg:#00ffff #ffffff",
        },
        extra_data_getter=[lambda: {"current_time": datetime.now().time().isoformat()}],
        replace_logger=False,
    )
    saya = Saya(app.broadcast)
    saya.install_behaviours(BroadcastBehaviour(app.broadcast))
    saya.install_behaviours(ConsoleBehaviour(console))
    saya.install_behaviours(GraiaSchedulerBehaviour(GraiaScheduler(app.loop, app.broadcast)))
    console.start()
    change_logger(basic_cfg.debug, True)  # 对logger进行调整，必须放在这里

    if modules_cfg.enabled:
        with saya.module_context():
            for module in os.listdir(modules_path):
                if module in modules_cfg.globalDisabledModules:
                    continue
                elif module == '__pycache__' or module[0] in ('!', '#', '.'):
                    continue
                elif Path.is_dir(Path(modules_path, module)):
                    saya.require(f'modules.{module}')
                elif Path.is_file(Path(modules_path, module)) and module[-3:] == '.py':
                    saya.require(f'modules.{module[:-3]}')

    app.launch_blocking()
    console.stop()
