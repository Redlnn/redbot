#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from creart import create
from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import (
    HttpClientConfig,
    WebsocketClientConfig,
    config,
)
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source
from graia.ariadne.model import Group, LogConfig, Member
from graia.broadcast import Broadcast
from graia.scheduler import GraiaScheduler
from graia.scheduler.timers import crontabify

from util import log_level_handler, replace_logger
from util.config import basic_cfg
from util.send_action import Safe

if basic_cfg.miraiApiHttp.account == 123456789:
    raise ValueError('在?¿ 填一下配置文件？')

bcc = create(Broadcast)
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
sche = create(GraiaScheduler)
replace_logger(level=0 if basic_cfg.debug else 20, richuru=True)  # 对logger进行调整，必须放在这里


@sche.schedule(crontabify('0 0 * * *'))
async def test():
    ...


@bcc.receiver(GroupMessage)
async def setu(app: Ariadne, group: Group, member: Member, message: MessageChain, source: Source):
    print(group)
    print(member)
    print(message.__repr__)
    print(source.__repr__)


app.launch_blocking()
