#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from random import randint

import regex
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain, Source
from graia.ariadne.message.parser.pattern import ElementMatch, RegexMatch
from graia.ariadne.message.parser.twilight import Sparkle, Twilight
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
    usage='@bot {主语}<介词>不<介词>{动作}\n如：@bot 我要不要去吃饭',
).register()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([ElementMatch(At), RegexMatch(r'(.+)?(?P<v>\S+)不(?P=v)(.+)?')]))],
        decorators=[group_blacklist(), MemberInterval.require(2)],
    )
)
async def main(app: Ariadne, group: Group, message: MessageChain):
    if not config_data['Modules']['HelpYouChoose']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['HelpYouChoose']['DisabledGroup']:
        if group.id in config_data['Modules']['HelpYouChoose']['DisabledGroup']:
            return

    re_match = regex.match(r'(.+)?(?P<v>\S+)不(?P=v)(.+)?', message.include(Plain).asDisplay().strip())
    if not re_match:
        return
    re_match = re_match.groups()
    subject = re_match[0].replace('我', '你') if re_match[0] else ''
    preposition = re_match[1]
    action = re_match[2].replace('我', '你') if re_match[2] else ''
    roll = randint(0, 100)
    if roll % 2 == 0:
        chain = MessageChain.create(Plain(subject + preposition + action))
    else:
        chain = MessageChain.create(Plain(subject + '不' + preposition + action))
    await app.sendGroupMessage(group, chain, quote=message.get(Source).pop(0))
