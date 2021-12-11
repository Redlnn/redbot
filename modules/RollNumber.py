#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用法：

在本Bot账号所在的任一一QQ群中发送 `!roll` 或 `!roll {任意字符}` 均可触发本插件功能
触发后会回复一个由0至100之间的任一随机整数
"""

import os
from random import randint

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Source
from graia.ariadne.message.parser.twilight import (
    RegexMatch,
    Sparkle,
    Twilight,
    WildcardMatch,
)
from graia.ariadne.model import Group
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from config import config_data
from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Rate import MemberInterval
from utils.ModuleRegister import Module

saya = Saya.current()
channel = Channel.current()

Module(
    name='随机数',
    config_name='RollNumber',
    file_name=os.path.basename(__file__),
    author=['Red_lnn'],
    description='获得一个随机数',
    usage='[!！.]roll {要roll的事件}',
).register()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle(match={'prefix': RegexMatch(r'[!！.]roll'), 'target': WildcardMatch()}))],
        decorators=[group_blacklist(), MemberInterval.require(2)],
    )
)
async def main(app: Ariadne, group: Group, message: MessageChain, target: WildcardMatch):
    if not config_data['Modules']['RollNumber']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['RollNumber']['DisabledGroup']:
        if group.id in config_data['Modules']['RollNumber']['DisabledGroup']:
            return
    if target.matched:
        chain = MessageChain.create(Plain(f'{target.result.asDisplay().strip()}的概率为：{randint(0, 100)}'))
    else:
        chain = MessageChain.create(Plain(str(randint(0, 100))))
    await app.sendGroupMessage(group, chain, quote=message.get(Source).pop(0))
