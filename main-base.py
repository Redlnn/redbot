#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

from graia.ariadne.app import Ariadne
from graia.ariadne.connection.config import (
    HttpClientConfig,
    WebsocketClientConfig,
    config,
)
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source
from graia.ariadne.model import Group, Member
from graia.broadcast import Broadcast

from util.ariadne_rewrite import CustomLogConfig
from util.config import basic_cfg
from util.logger_rewrite import rewrite_ariadne_logger
from util.send_action import Safe

if basic_cfg.miraiApiHttp.account == 123456789:
    raise ValueError('在?¿ 填一下配置文件？')

loop = asyncio.new_event_loop()
bcc = Broadcast(loop=loop)

Ariadne.config(loop=loop, broadcast=bcc, install_log=True)
app = Ariadne(
    connection=config(
        basic_cfg.miraiApiHttp.account,  # 你的机器人的 qq 号
        basic_cfg.miraiApiHttp.verifyKey,  # 填入 verifyKey
        HttpClientConfig(host=basic_cfg.miraiApiHttp.host),
        WebsocketClientConfig(host=basic_cfg.miraiApiHttp.host),
    ),
    log_config=CustomLogConfig(log_level='DEBUG' if basic_cfg.debug else 'INFO'),
)
app.default_send_action = Safe
rewrite_ariadne_logger(basic_cfg.debug)  # 对logger进行调整，必须放在这里


@bcc.receiver(GroupMessage)
async def setu(app: Ariadne, group: Group, member: Member, message: MessageChain, source: Source):
    print(group)
    print(member)
    print(message.__repr__)
    print(source.__repr__)


app.launch_blocking()
