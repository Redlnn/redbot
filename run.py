#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path

from graia.ariadne.app import Ariadne
from graia.ariadne.model import MiraiSession
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler import GraiaScheduler
from graia.scheduler.saya import GraiaSchedulerBehaviour

from config import config_data

if __name__ == '__main__':
    app = Ariadne(
        MiraiSession(
            host=config_data['Basic']['MiraiApiHttp']['Host'],  # 填入 httpapi 服务运行的地址
            account=config_data['Basic']['MiraiApiHttp']['Account'],  # 你的机器人的 qq 号
            verify_key=config_data['Basic']['MiraiApiHttp']['VerifyKey'],  # 填入 verifyKey
        ),
        chat_log_config=None if config_data['Basic']['LogChat'] else False,
    )
    saya = Saya(app.broadcast)
    saya.install_behaviours(BroadcastBehaviour(app.broadcast))
    saya.install_behaviours(GraiaSchedulerBehaviour(GraiaScheduler(app.loop, app.broadcast)))
    from utils.logger import logger

    async def main() -> None:
        await app.launch()
        await app.lifecycle()

    if not Path.exists(Path(Path.cwd(), 'data')):
        Path.mkdir(Path(Path.cwd(), 'data'))

    if config_data['Modules']['Enabled']:
        with saya.module_context():
            for module in os.listdir(Path(Path.cwd(), 'modules')):
                if module in ('database.py', '__pycache__') or module[0] in ('!', '#', '.'):
                    continue
                elif Path.is_dir(Path(Path.cwd(), 'modules', module)):
                    saya.require(f'modules.{module}')
                elif Path.is_file(Path(Path.cwd(), 'modules', module)) and module[-3:] == '.py':
                    saya.require(f'modules.{module[:-3]}')
    logger.info('正在启动 Ariadne...')
    app.launch_blocking()
