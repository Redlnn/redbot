#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用法：

在本Bot账号所在的任一一QQ群中发送 `!roll` 或 `!roll {任意字符}` 均可触发本插件功能
触发后会回复一个由0至100之间的任一随机整数
"""

from random import randint

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Source
from graia.ariadne.message.parser.pattern import RegexMatch
from graia.ariadne.message.parser.twilight import Sparkle, Twilight
from graia.ariadne.model import Group
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Rate import MemberInterval

channel = Channel.current()

channel.name('随机数')
channel.author('Red_lnn')
channel.description('获得一个随机数\n用法：[!！.]roll {要roll的事件}')

# 生效的群组，若为空，即()，则在所有群组生效
# 格式为：active_group = (123456, 456789, 789012)
active_group = ()


class Match(Sparkle):
    prefix = RegexMatch(r'^[!！.]roll$')
    roll_target = RegexMatch(r'\ \S+', optional=True)


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(Match)],
                decorators=[group_blacklist(), MemberInterval.require(2, send_alert=False)],
        )
)
async def main(app: Ariadne, group: Group, message: MessageChain, sparkle: Sparkle):
    if group.id not in active_group and active_group:
        return
    if sparkle.roll_target.matched:
        chain = MessageChain.create([Plain(f'{sparkle.roll_target.result.asDisplay().strip()}的概率为：{randint(0, 100)}')])
    else:
        chain = MessageChain.create([Plain(str(randint(0, 100)))])
    await app.sendGroupMessage(group, chain, quote=message.get(Source).pop(0))
