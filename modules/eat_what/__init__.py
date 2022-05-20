#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
from os.path import dirname, split
from pathlib import Path

from aiofile import async_open
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Source
from graia.ariadne.message.parser.twilight import RegexMatch, SpacePolicy, Twilight
from graia.ariadne.model import Group
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from util.control import DisableModule
from util.control.permission import GroupPermission
from util.module_register import Module

channel = Channel.current()
module_name = split(dirname(__file__))[-1]

Module(
    name='吃啥',
    file_name=module_name,
    author=['Red_lnn'],
    usage='[!！.]吃啥',
).register()


async def get_food():
    async with async_open(Path(Path(__file__).parent, 'foods.txt')) as afp:
        foods = await afp.read()
    return random.choice(foods.strip().split('\n'))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]吃啥').space(SpacePolicy.NOSPACE)])],
        decorators=[GroupPermission.require(), DisableModule.require(module_name)],
    )
)
async def main(app: Ariadne, group: Group, source: Source):
    food = await get_food()
    chain = MessageChain.create(Plain(f'吃{food}'))
    await app.sendMessage(group, chain, quote=source)
