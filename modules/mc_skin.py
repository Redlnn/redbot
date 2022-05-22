#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
mc皮肤查询

移植自 https://github.com/BlueGlassBlock/Xenon/blob/master/module/mc_skin.py
"""

from asyncio.exceptions import TimeoutError

import orjson
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import (
    ArgResult,
    ArgumentMatch,
    RegexMatch,
    RegexResult,
    SpacePolicy,
    Twilight,
)
from graia.ariadne.model import Group
from graia.saya.builtins.broadcast import ListenerSchema
from graia.saya.channel import Channel

from util.control import DisableModule
from util.control.interval import MemberInterval
from util.control.permission import GroupPermission
from util.get_aiohtto_session import get_session

channel = Channel.current()

channel.meta['name'] = 'mc正版皮肤获取'
channel.meta['author'] = ['BlueGlassBlock']
channel.meta['description'] = '[.!！]skin <name> {option}\noption: original|body|head|avatar'

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
                [
                    RegexMatch(r'[.!！]skin').space(SpacePolicy.FORCE),
                    'name' @ RegexMatch(r'[0-9a-zA-Z_]+'),
                    ArgumentMatch(
                        '--type', '-T', default='head', type=str, choices=['original', 'body', 'head', 'avatar']
                    ).param(
                        'option'
                    ),  # 为了black格式化后好看所以用了param
                ],
            )
        ],
        decorators=[GroupPermission.require(), MemberInterval.require(30), DisableModule.require(channel.module)],
    )
)
async def get_skin(app: Ariadne, group: Group, name: RegexResult, option: ArgResult):
    session = get_session()
    try:
        async with session.get(UUID_ADDRESS_STRING.format(name=name.result.asDisplay())) as resp:  # type: ignore
            uuid = orjson.loads(await resp.text())["id"]
        url = RENDER_ADDR[option.result].format(uuid=uuid)  # type: ignore
        await app.sendMessage(group, MessageChain.create(Image(url=url)))
    except TimeoutError as e:
        await app.sendMessage(group, MessageChain.create(f"无法获取皮肤: {e}"))
