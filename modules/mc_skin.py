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
from graia.ariadne.util.saya import decorate, dispatch, listen
from graia.saya.channel import Channel

from util import GetAiohttpSession
from util.control import require_disable
from util.control.interval import MemberInterval
from util.control.permission import GroupPermission

channel = Channel.current()

channel.meta['name'] = 'mc正版皮肤获取'
channel.meta['author'] = ['BlueGlassBlock']
channel.meta['description'] = '[.!！]skin <name> {option}\noption: original|body|head|avatar'

UUID_ADDRESS_STRING = 'https://api.mojang.com/users/profiles/minecraft/{name}'

RENDER_ADDR = {
    'original': 'https://crafatar.com/skins/{uuid}',
    'body': 'https://crafatar.com/renders/body/{uuid}?overlay',
    'head': 'https://crafatar.com/renders/head/{uuid}?overlay',
    'avatar': 'https://crafatar.com/avatars/{uuid}?overlay',
}


@listen(GroupMessage)
@dispatch(
    Twilight(
        RegexMatch(r'[.!！]skin').space(SpacePolicy.FORCE),
        'name' @ RegexMatch(r'[0-9a-zA-Z_]+'),
        ArgumentMatch('--type', '-T', default='head', type=str, choices=['original', 'body', 'head', 'avatar']).param(
            'option'
        ),  # 为了black格式化后好看所以用了param
    )
)
@decorate(GroupPermission.require(), MemberInterval.require(30), require_disable(channel.module))
async def get_skin(app: Ariadne, group: Group, name: RegexResult, option: ArgResult[str]):
    if name.result is None or option.result is None:
        return
    try:
        session = GetAiohttpSession.get_session()
        async with session.get(UUID_ADDRESS_STRING.format(name=str(name.result))) as resp:
            uuid = orjson.loads(await resp.text())['id']
        url = RENDER_ADDR[option.result].format(uuid=uuid)
        await app.send_message(group, MessageChain(Image(url=url)))
    except TimeoutError:
        await app.send_message(group, MessageChain('连接API超时'))
    except Exception as e:
        await app.send_message(group, MessageChain(f'无法获取皮肤: {e}'))
