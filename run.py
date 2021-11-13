#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os

from graia.ariadne.adapter import CombinedAdapter
from graia.ariadne.app import Ariadne
from graia.ariadne.exception import AccountNotFound
from graia.ariadne.model import MiraiSession
from graia.broadcast import Broadcast
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler import GraiaScheduler
from graia.scheduler.saya import GraiaSchedulerBehaviour
from utils.logger import logger

from config import config_data

if __name__ == '__main__':
    logger.info('初始化...')
    loop = asyncio.new_event_loop()
    bcc = Broadcast(loop=loop, debug_flag=config_data['Basic']['Debug'])
    scheduler = GraiaScheduler(loop, bcc)
    saya = Saya(bcc)

    saya.install_behaviours(BroadcastBehaviour(bcc))
    saya.install_behaviours(GraiaSchedulerBehaviour(scheduler))

    if config_data['Basic']['LogChat']:
        app = Ariadne.create(
                broadcast=bcc,
                session=MiraiSession(
                        host=config_data['Basic']['MiraiApiHttp']['Host'],  # 填入 httpapi 服务运行的地址
                        account=config_data['Basic']['MiraiApiHttp']['Account'],  # 你的机器人的 qq 号
                        verify_key=config_data['Basic']['MiraiApiHttp']['VerifyKey']  # 填入 verifyKey
                )
        )
    else:
        app = Ariadne(
            broadcast=bcc,
            chat_log_config=False,
            adapter=CombinedAdapter(
                bcc,
                MiraiSession(
                        host=config_data['Basic']['MiraiApiHttp']['Host'],  # 填入 httpapi 服务运行的地址
                        account=config_data['Basic']['MiraiApiHttp']['Account'],  # 你的机器人的 qq 号
                        verify_key=config_data['Basic']['MiraiApiHttp']['VerifyKey']  # 填入 verifyKey
                ),
            ),
        )

    async def main() -> None:
        await app.launch()
        await app.lifecycle()

    if not os.path.exists(os.path.join(os.getcwd(), 'data')):
        os.mkdir(os.path.join(os.getcwd(), 'data'))

    if config_data['Modules']['Enabled']:
        logger.info('加载插件中...')
        with saya.module_context():
            for module in os.listdir(os.path.join('modules')):
                if module in ('database.py', '__pycache__') or module[0] in ('!', '#', '.'):
                    continue
                elif os.path.isdir(os.path.join('modules', module)):
                    saya.require(f'modules.{module}')
                elif os.path.isfile(os.path.join('modules', module)) and module[-3:] == '.py':
                    saya.require(f'modules.{module[:-3]}')
    logger.info('正在启动 Ariadne...')

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info('正在退出中...')
        loop.run_until_complete(app.stop())
        logger.info('Bye~')
        logger.complete()
        exit()
    except AccountNotFound:
        logger.critical('Ariadne 启动失败，无法连接到 Mirai-Api-Http：Account Not Found')
        logger.info("正在退出...")
        logger.complete()
        exit()
