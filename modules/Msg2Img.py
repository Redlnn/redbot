#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import basename
from typing import List

import aiohttp
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import (
    RegexMatch,
    Sparkle,
    Twilight,
    WildcardMatch,
)
from graia.ariadne.model import Group
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from utils.config import get_modules_config
from utils.control.interval import GroupInterval
from utils.control.permission import GroupPermission
from utils.module_register import Module
from utils.text2img import async_generate_img

channel = Channel.current()
modules_cfg = get_modules_config()
module_name = basename(__file__)

Module(
    name='消息转图片',
    file_name=module_name,
    author=['Red_lnn'],
    description='仿锤子便签样式的消息转图片，支持纯文本与图像',
    usage='[!！.]img <文本、图像>',
).register()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                Sparkle(
                    [RegexMatch(r'[!！.]img\ ')],
                    {
                        'content': WildcardMatch(),
                    },
                )
            )
        ],
        decorators=[GroupPermission.require(), GroupInterval.require(15)],
    )
)
async def main(app: Ariadne, group: Group, content: RegexMatch):
    if module_name in modules_cfg.disabledGroups:
        if group.id in modules_cfg.disabledGroups[module_name]:
            return
    img_list: List[str | bytes] = []
    async with aiohttp.ClientSession() as session:
        for i in content.result:
            if type(i) == Image:
                async with session.get(i.url) as resp:
                    img_list.append(await resp.content.read())
            else:
                img_list.append(i.asDisplay())

    if img_list:
        img_bytes = await async_generate_img(img_list)
        await app.sendGroupMessage(group, MessageChain.create(Image(data_bytes=img_bytes)))
