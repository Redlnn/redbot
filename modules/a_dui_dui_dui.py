#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.twilight import RegexMatch, SpacePolicy, Twilight
from graia.ariadne.model import Group
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from util.control import require_disable
from util.control.permission import GroupPermission

channel = Channel.current()

channel.meta['author'] = ['Red_lnn', 'KuborKelp']
channel.meta['name'] = '啊对对对'
channel.meta['description'] = '啊对对对'


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(RegexMatch(r'[啊阿]对+').space(SpacePolicy.NOSPACE))],
        decorators=[GroupPermission.require(), require_disable(channel.module)],
    )
)
async def main(app: Ariadne, group: Group, message: MessageChain):
    message = message.copy()
    message.__root__.append(Plain('对'))
    await app.send_message(group, message)
