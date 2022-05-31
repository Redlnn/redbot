#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from random import randint

import regex as re
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain, Source
from graia.ariadne.message.parser.twilight import (
    ElementMatch,
    ElementResult,
    SpacePolicy,
    Twilight,
    WildcardMatch,
)
from graia.ariadne.model import Group
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from util.config import basic_cfg
from util.control import require_disable
from util.control.permission import GroupPermission

channel = Channel.current()

channel.meta['name'] = '帮你做选择'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = '@bot {主语}<介词>不<介词>{动作}\n如：@bot 我要不要去吃饭\n@bot 我有没有机会'


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight('at' @ ElementMatch(At).space(SpacePolicy.FORCE), 'any' @ WildcardMatch())],
        decorators=[GroupPermission.require(), require_disable(channel.module)],
    )
)
async def main(app: Ariadne, group: Group, source: Source, message: MessageChain, at: ElementResult):
    if at.result.target != basic_cfg.miraiApiHttp.account:  # type: ignore
        return
    msg = message.include(Plain).display.strip()
    re1_match = re.match(r'(.+)?(?P<v>\S+)不(?P=v)(.+)?', msg)
    re2_match = re.match(r'(.+)?(?P<v>有)(没|木)(?P=v)(.+)?', msg)
    if re1_match:
        re1_match = re1_match.groups()
        subject = re1_match[0].replace('我', '你') if re1_match[0] else ''
        preposition = re1_match[1]
        action = re1_match[2].replace('我', '你') if re1_match[2] else ''
        roll = randint(0, 100)
        if roll % 2 == 0:
            chain = MessageChain(Plain(subject + preposition + action))
        else:
            chain = MessageChain(Plain(subject + '不' + preposition + action))
    elif re2_match:
        re2_match = re2_match.groups()
        subject = re2_match[0].replace('我', '你') if re2_match[0] else ''
        preposition = re2_match[1]
        action = re2_match[3].replace('我', '你') if re2_match[2] else ''
        roll = randint(0, 100)
        if roll % 2 == 0:
            chain = MessageChain(Plain(subject + preposition + action))
        else:
            chain = MessageChain(Plain(subject + re2_match[2] + preposition + action))
    else:
        return
    await app.send_message(group, chain, quote=source)
