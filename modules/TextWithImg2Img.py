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

from config import config_data
from modules.BotManage import Module
from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Rate import GroupInterval
from utils.TextWithImg2Img import async_generate_img

saya = Saya.current()
channel = Channel.current()

Module(
        name='消息转图片',
        config_name='TextWithImg2Img',
        author=['Red_lnn'],
        description='仿锤子便签样式的消息转图片，支持纯文本与图像',
        usage='[!！.]img <文本、图像>'
).registe()


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
    if not config_data['Modules']['TextWithImg2Img']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['TextWithImg2Img']['DisabledGroup']:
        if group.id in config_data['Modules']['TextWithImg2Img']['DisabledGroup']:
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
