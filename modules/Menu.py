#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from utils.TextWithImg2Img import async_generate_img, hr

saya = Saya.current()
channel = Channel.current()

channels = saya.channels


class Match(Sparkle):
    prefix = RegexMatch(r'[!！.](菜单|menu)')


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(Match)],
                decorators=[group_blacklist(), GroupInterval.require(5, send_alert=False)],
        )
)
async def main(app: Ariadne, group: Group):
    msg_send = '-= Red_lnn Bot 指令菜单 =-\n' + hr + '\n'
    for _ in channels.keys():
        if channels[_].module in (channel.module, 'module.test'):
            continue
        msg_send += f'模块名: {channels[_]._name}\n描述：\n'
        for i in channels[_]._description.split("\n"):
            msg_send += f'    {i}\n'
        msg_send += hr + '\n'

    img_io = await async_generate_img([msg_send])
    await app.sendGroupMessage(group, MessageChain.create(Image(data_bytes=img_io.getvalue())))
