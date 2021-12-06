#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from io import BytesIO

import httpx
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.pattern import RegexMatch, WildcardMatch
from graia.ariadne.message.parser.twilight import Sparkle, Twilight
from graia.ariadne.model import Group
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from config import config_data
from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Rate import GroupInterval
from utils.ModuleRegister import Module
from utils.TextWithImg2Img import async_generate_img

saya = Saya.current()
channel = Channel.current()

Module(
    name='消息转图片',
    config_name='TextWithImg2Img',
    file_name=os.path.basename(__file__),
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
                    {
                        'prefix': RegexMatch(r'[!！.]img\ '),
                        'content': WildcardMatch(),
                    }
                )
            )
        ],
        decorators=[group_blacklist(), GroupInterval.require(15)],
    )
)
async def main(app: Ariadne, group: Group, content: RegexMatch):
    if not config_data['Modules']['TextWithImg2Img']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['TextWithImg2Img']['DisabledGroup']:
        if group.id in config_data['Modules']['TextWithImg2Img']['DisabledGroup']:
            return
    img_list = []
    for i in content.result:
        if type(i) == Image:
            img = await httpx.AsyncClient().get(i.url)
            img_list.append(BytesIO(img.content))
        else:
            img_list.append(i.asDisplay())

    if img_list:
        img_io = await async_generate_img(img_list)
        await app.sendGroupMessage(group, MessageChain.create(Image(data_bytes=img_io.getvalue())))
