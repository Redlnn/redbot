#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
from pathlib import Path

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Source
from graia.ariadne.message.parser.pattern import RegexMatch
from graia.ariadne.message.parser.twilight import Sparkle, Twilight
from graia.ariadne.model import Group
from graia.ariadne.util.async_exec import io_bound
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from config import config_data
from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Rate import MemberInterval
from utils.ModuleRegister import Module

saya = Saya.current()
channel = Channel.current()

Module(
    name='吃啥',
    config_name='EatWhat',
    file_name=os.path.basename(__file__),
    author=['Red_lnn'],
    usage='[!！.]吃啥',
).register()


@io_bound
def get_food():
    with open(Path(Path(__file__).parent, 'foods.txt')) as f:
        foods = f.readlines()
    food = random.choice(foods)
    return food.rstrip()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]吃啥')]))],
        decorators=[group_blacklist(), MemberInterval.require(2)],
    )
)
async def main(app: Ariadne, group: Group, message: MessageChain):
    if not config_data['Modules']['EatWhat']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['EatWhat']['DisabledGroup']:
        if group.id in config_data['Modules']['EatWhat']['DisabledGroup']:
            return
    food = await get_food()
    chain = MessageChain.create(Plain(f'吃{food}'))
    await app.sendGroupMessage(group, chain, quote=message.get(Source).pop(0))
