#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from random import randint

import regex as re
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain, Source
from graia.ariadne.message.parser.twilight import (
    ElementMatch,
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
    name='帮你做选择',
    config_name='HelpYouChoose',
    file_name=os.path.basename(__file__),
    author=['Red_lnn'],
    usage='@bot {主语}<介词>不<介词>{动作}\n如：@bot 我要不要去吃饭\n@bot 我有没有机会',
).register()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle(match={'at': ElementMatch(At), 'any': WildcardMatch()}))],
        decorators=[group_blacklist(), MemberInterval.require(2)],
    )
)
async def main(app: Ariadne, group: Group, message: MessageChain, at: ElementMatch):
    if not config_data['Modules']['HelpYouChoose']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['HelpYouChoose']['DisabledGroup']:
        if group.id in config_data['Modules']['HelpYouChoose']['DisabledGroup']:
            return
    if at.result.target != config_data['Basic']['MiraiApiHttp']['Account']:
        return
    msg = message.include(Plain).asDisplay().strip()
    re1_match = re.match(r'(.+)?(?P<v>\S+)不(?P=v)(.+)?', msg)
    re2_match = re.match(r'(.+)?(?P<v>有)(没|木)(?P=v)(.+)?', msg)
    if re1_match:
        re1_match = re1_match.groups()
        subject = re1_match[0].replace('我', '你') if re1_match[0] else ''
        preposition = re1_match[1]
        action = re1_match[2].replace('我', '你') if re1_match[2] else ''
        roll = randint(0, 100)
        if roll % 2 == 0:
            chain = MessageChain.create(Plain(subject + preposition + action))
        else:
            chain = MessageChain.create(Plain(subject + '不' + preposition + action))
    elif re2_match:
        re2_match = re2_match.groups()
        subject = re2_match[0].replace('我', '你') if re2_match[0] else ''
        preposition = re2_match[1]
        action = re2_match[3].replace('我', '你') if re2_match[2] else ''
        roll = randint(0, 100)
        if roll % 2 == 0:
            chain = MessageChain.create(Plain(subject + preposition + action))
        else:
            chain = MessageChain.create(Plain(subject + re2_match[2] + preposition + action))
    else:
        return
    await app.sendGroupMessage(group, chain, quote=message.get(Source).pop(0))
