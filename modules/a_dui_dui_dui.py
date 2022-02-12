#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import basename

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.twilight import RegexMatch, Sparkle, Twilight
from graia.ariadne.model import Group
from graia.broadcast.interrupt import InterruptControl
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from util.config import ModulesConfig
from util.control.permission import GroupPermission
from util.module_register import Module

saya = Saya.current()
channel = Channel.current()
inc = InterruptControl(saya.broadcast)

modules_cfg = ModulesConfig()
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
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[啊阿]对+')]))],
        decorators=[GroupPermission.require()],
    )
)
async def main(app: Ariadne, group: Group, message: MessageChain):
    if module_name in modules_cfg.disabledGroups:
        if group.id in modules_cfg.disabledGroups[module_name]:
            return
    await app.sendMessage(group, message + MessageChain.create(Plain('对')))
