#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BytesIO

import httpx
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.pattern import RegexMatch
from graia.ariadne.message.parser.twilight import Sparkle, Twilight
from graia.ariadne.model import Group
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Rate import GroupInterval
from utils.TextWithImg2Img import async_generate_img

saya = Saya.current()
channel = Channel.current()

channel.name('消息转图片')
channel.author('Red_lnn')
channel.description('用法：[!！.]img <文本、图片>}')

# 生效的群组，若为空，即()，则在所有群组生效
# 格式为：active_group = (123456, 456789, 789012)
active_group = ()


class Match(Sparkle):
    prefix = RegexMatch(r'[!！.]img\ ')
    any = RegexMatch(r'.+')


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(Match)],
                decorators=[group_blacklist(), GroupInterval.require(15)],
        )
)
async def main(app: Ariadne, group: Group, sparkle: Sparkle):
    if group.id not in active_group and active_group:
        return
    img_list = []
    for i in sparkle.any.result:
        if type(i) == Image:
            img = await httpx.AsyncClient().get(i.url)
            img_list.append(BytesIO(img.content))
        else:
            img_list.append(i.asDisplay())

    if img_list:
        img_io = await async_generate_img(img_list)
        await app.sendGroupMessage(group, MessageChain.create(Image(data_bytes=img_io.getvalue())))
