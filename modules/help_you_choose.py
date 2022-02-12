#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import basename
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
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from util.config import BasicConfig, ModulesConfig
from util.control.permission import GroupPermission
from util.module_register import Module

channel = Channel.current()
modules_cfg = ModulesConfig()
module_name = basename(__file__)[:-3]
basic_cfg = BasicConfig()

Module(
    name='帮你做选择',
    file_name=module_name,
    author=['Red_lnn'],
    usage='@bot {主语}<介词>不<介词>{动作}\n如：@bot 我要不要去吃饭\n@bot 我有没有机会',
).register()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle({'at': ElementMatch(At), 'any': WildcardMatch()}))],
        decorators=[GroupPermission.require()],
    )
)
async def main(app: Ariadne, group: Group, source: Source, message: MessageChain, at: ElementMatch):
    if module_name in modules_cfg.disabledGroups:
        if group.id in modules_cfg.disabledGroups[module_name]:
            return
    if at.result.target != basic_cfg.miraiApiHttp.account:
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
    await app.sendMessage(group, chain, quote=source)
