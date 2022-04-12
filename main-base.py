#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Source
from graia.ariadne.model import Group, Member, MiraiSession

from util.config import basic_cfg
from util.logger_rewrite import rewrite_ariadne_logger
from util.send_action import Safe

if basic_cfg.miraiApiHttp.account == 123456789:
    raise ValueError('在?¿ 填一下配置文件？')

app = Ariadne(
    MiraiSession(
        host=basic_cfg.miraiApiHttp.host,  # 填入 httpapi 服务运行的地址
        account=basic_cfg.miraiApiHttp.account,  # 你的机器人的 qq 号
        verify_key=basic_cfg.miraiApiHttp.verifyKey,  # 填入 verifyKey
    ),
    chat_log_config=None if basic_cfg.logChat else False,
)
app.adapter.log = False  # type: ignore
app.default_send_action = Safe  # type: ignore
bcc = app.broadcast

rewrite_ariadne_logger(basic_cfg.debug, False)  # 对logger进行调整，必须放在这里


@bcc.receiver(GroupMessage)
async def setu(app: Ariadne, group: Group, member: Member, message: MessageChain, source: Source):
    print(group)
    print(member)
    print(message.__repr__)
    print(source.__repr__)


app.launch_blocking()
