#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
from os.path import dirname
from pathlib import Path

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Source
from graia.ariadne.message.parser.twilight import RegexMatch, Sparkle, Twilight
from graia.ariadne.model import Group
from graia.ariadne.util.async_exec import io_bound
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from utils.config import get_modules_config
from utils.control.interval import MemberInterval
from utils.control.permission import GroupPermission
from utils.module_register import Module
from utils.send_message import safeSendGroupMessage

channel = Channel.current()
modules_cfg = get_modules_config()
module_name = dirname(__file__)

Module(
    name='吃啥',
    file_name=module_name,
    author=['Red_lnn'],
    usage='[!！.]吃啥',
).register()


@io_bound
def get_food():
    with open(Path(Path(__file__).parent, 'foods.txt')) as fp:
        foods = fp.readlines()
    food = random.choice(foods)
    return food.rstrip()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]吃啥')]))],
        decorators=[GroupPermission.require(), MemberInterval.require(2)],
    )
)
async def main(group: Group, source: Source):
    if module_name in modules_cfg.disabledGroups:
        if group.id in modules_cfg.disabledGroups[module_name]:
            return
    food = await get_food()
    chain = MessageChain.create(Plain(f'吃{food}'))
    await safeSendGroupMessage(group, chain, quote=source)
