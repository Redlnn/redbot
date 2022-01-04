#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from os.path import basename
from typing import List

from graia.ariadne.app import Ariadne
from graia.ariadne.context import adapter_ctx
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Plain, Quote, Source
from graia.ariadne.message.parser.twilight import (
    RegexMatch,
    Sparkle,
    Twilight,
    WildcardMatch,
)
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt import InterruptControl
from graia.broadcast.interrupt.waiter import Waiter
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from utils.config import get_modules_config
from utils.control.interval import GroupInterval
from utils.control.permission import GroupPermission
from utils.module_register import Module
from utils.text2img import async_generate_img

saya = Saya.current()
channel = Channel.current()
inc = InterruptControl(saya.broadcast)

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
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.](文本转图片|消息转图片)')]))],
        decorators=[GroupPermission.require(), GroupInterval.require(15)],
    )
)
async def main(app: Ariadne, group: Group, member: Member, message: MessageChain):
    if module_name in modules_cfg.disabledGroups:
        if group.id in modules_cfg.disabledGroups[module_name]:
            return

    @Waiter.create_using_function([GroupMessage])
    async def waiter(waiter_group: Group, waiter_member: Member, waiter_message: MessageChain):
        if waiter_group.id == group.id and waiter_member.id == member.id:
            return waiter_message.include(Plain, At, Image)

    await app.sendGroupMessage(group, MessageChain.create(Plain('请发送要转换的内容')), quote=message.get(Source).pop(0))
    try:
        answer: MessageChain = await asyncio.wait_for(inc.wait(waiter), timeout=10)
    except asyncio.exceptions.TimeoutError:
        await app.sendGroupMessage(group, MessageChain.create(Plain('已超时取消')), quote=message.get(Source).pop(0))
        return

    if len(answer) == 0:
        await app.sendGroupMessage(group, MessageChain.create(Plain('你所发送的消息的类型错误')), quote=message.get(Source).pop(0))
        return

    img_list: List[str | bytes] = []
    session = adapter_ctx.get().session
    for i in answer.__root__:
        if type(i) == Image:
            async with session.get(i.url) as resp:
                img_list.append(await resp.content.read())
        else:
            img_list.append(i.asDisplay())

    if img_list:
        img_bytes = await async_generate_img(img_list)
        await app.sendGroupMessage(group, MessageChain.create(Image(data_bytes=img_bytes)))
