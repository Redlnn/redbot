#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import basename

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.twilight import RegexMatch, SpacePolicy, Twilight
from graia.ariadne.model import Group
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from util.control import DisableModule
from util.control.permission import GroupPermission
from util.module_register import Module

channel = Channel.current()

module_name = basename(__file__)[:-3]

Module(
    name='啊对对对',
    file_name=module_name,
    author=['Red_lnn', 'KuborKelp'],
    usage='啊对对对',
).register()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[啊阿]对+').space(SpacePolicy.NOSPACE)])],
        decorators=[GroupPermission.require(), DisableModule.require(module_name)],
    )
)
async def main(app: Ariadne, group: Group, message: MessageChain):
    await app.sendMessage(group, message + MessageChain.create(Plain('对')))
