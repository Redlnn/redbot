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
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from config import config_data
from modules.BotManage import Module
from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Rate import MemberInterval

saya = Saya.current()
channel = Channel.current()

Module(
        name='随机数',
        config_name='RollNumber',
        author=['Red_lnn'],
        description='获得一个随机数',
        usage='[!！.]roll {要roll的事件}'
).registe()


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]roll'), RegexMatch(r'\ \S+', optional=True)]))],
                decorators=[group_blacklist(), MemberInterval.require(2)],
        )
)
async def main(app: Ariadne, group: Group, message: MessageChain, sparkle: Sparkle):
    if not config_data['Modules']['RollNumber']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['RollNumber']['DisabledGroup']:
        if group.id in config_data['Modules']['RollNumber']['DisabledGroup']:
            return
    if sparkle._check_1.matched:
        chain = MessageChain.create([Plain(f'{sparkle._check_1.result.asDisplay().strip()}的概率为：{randint(0, 100)}')])
    else:
        chain = MessageChain.create([Plain(str(randint(0, 100)))])
    await app.sendGroupMessage(group, chain, quote=message.get(Source).pop(0))
