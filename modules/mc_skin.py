#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
mc皮肤查询

移植自 https://github.com/BlueGlassBlock/Xenon/blob/master/module/mc_skin.py
"""

from os.path import basename

import orjson
from graia.ariadne.adapter import Adapter
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import (
    ArgumentMatch,
    RegexMatch,
    Sparkle,
    Twilight,
)
from graia.ariadne.model import Group
from graia.saya.builtins.broadcast import ListenerSchema
from graia.saya.channel import Channel

from util.control.interval import MemberInterval
from util.control.permission import GroupPermission
from util.module_register import Module

channel = Channel.current()
module_name = basename(__file__)[:-3]

Module(
    name='mc正版皮肤获取',
    file_name=module_name,
    author=['BlueGlassBlock'],
    usage='[.!！]skin <name> {option}\noption: original|body|head|avatar',
).register()

UUID_ADDRESS_STRING = "https://api.mojang.com/users/profiles/minecraft/{name}"

RENDER_ADDR = {
    "original": "https://crafatar.com/skins/{uuid}",
    "body": "https://crafatar.com/renders/body/{uuid}?overlay",
    "head": "https://crafatar.com/renders/head/{uuid}?overlay",
    "avatar": "https://crafatar.com/avatars/{uuid}?overlay",
}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                Sparkle(
                    [RegexMatch(r'[.!！]skin')],
                    {
                        'name': RegexMatch(r'^[0-9a-zA-Z_]+$'),
                        'option': ArgumentMatch('--type', '-T', default='head', regex=r'(original|body|head|avatar)'),
                    },
                ),
            )
        ],
        decorators=[GroupPermission.require(), MemberInterval.require(30)],
    )
)
async def get_skin(app: Ariadne, group: Group, name: RegexMatch, option: ArgumentMatch):
    session = Ariadne.get_running(Adapter).session
    try:
        uuid_resp = await session.get(UUID_ADDRESS_STRING.format(name=name.result.asDisplay()))
        uuid = orjson.loads(await uuid_resp.text())["id"]
        url = RENDER_ADDR[option.result.asDisplay()].format(uuid=uuid)
        await app.sendMessage(group, MessageChain.create(Image(url=url)))
    except Exception as e:
        await app.sendMessage(group, MessageChain.create(f"无法获取皮肤: {e!r}"))
