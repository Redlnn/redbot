#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用法：

在本Bot账号所在的任一一QQ群中发送 `!roll` 或 `!roll {任意字符}` 均可触发本插件功能
触发后会回复一个由0至100之间的任一随机整数
"""

from os.path import basename
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
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from util.config import get_modules_config
from util.control.interval import MemberInterval
from util.control.permission import GroupPermission
from util.module_register import Module

channel = Channel.current()
modules_cfg = get_modules_config()
module_name = basename(__file__)[:-3]

Module(
    name='随机数',
    file_name=module_name,
    author=['Red_lnn'],
    description='获得一个随机数',
    usage='[!！.]roll {要roll的事件}',
).register()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]roll')], {'target': WildcardMatch()}))],
        decorators=[GroupPermission.require(), MemberInterval.require(2)],
    )
)
async def main(app: Ariadne, group: Group, source: Source, target: WildcardMatch):
    if module_name in modules_cfg.disabledGroups:
        if group.id in modules_cfg.disabledGroups[module_name]:
            return
    if target.matched:
        chain = MessageChain.create(Plain(f'{target.result.asDisplay().strip()}的概率为：{randint(0, 100)}'))
    else:
        chain = MessageChain.create(Plain(str(randint(0, 100))))
    await app.sendMessage(group, chain, quote=source)
