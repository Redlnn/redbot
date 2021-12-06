#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from asyncio import Lock
from pathlib import Path

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Plain
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt import InterruptControl
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from config import config_data
from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Rate import ManualInterval
from utils.ModuleRegister import Module

from .ding import ding

lock: Lock = Lock()
saya = Saya.current()
channel = Channel.current()
inc = InterruptControl(saya.broadcast)

Module(
    name='用你的头像生成点啥',
    config_name='AvatarImgGen',
    file_name=os.path.dirname(__file__),
    author=['Red_lnn', 'SereinFish'],
    description='用你的头像生成一些有趣的图片',
    usage=('[!！.]顶 At/QQ号 —— 让猫猫虫咖波顶着你的头像耍'),
    can_disable=False,
).register()

func = {
    '顶': ding,
}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        decorators=[group_blacklist()],
    )
)
async def main(app: Ariadne, group: Group, member: Member, message: MessageChain):
    if not config_data['Modules']['AvatarImgGen']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['AvatarImgGen']['DisabledGroup']:
        if group.id in config_data['Modules']['AvatarImgGen']['DisabledGroup']:
            return

    if not message.has(Plain):
        return
    elif message.asDisplay()[0] not in ('!', '！', '.'):
        return

    split_message = message.asDisplay().split(' ')
    if len(split_message) != 2:
        return
    elif split_message[0][1:] not in func.keys():
        return

    if message.has(At):
        target = message.getFirst(At).target
    elif split_message[1].isdigit():
        target = split_message[1]
    else:
        return

    rate_limit, remaining_time = ManualInterval.require(f'AvatarImgGen_{member.id}', 30, 1)
    if not rate_limit:
        await app.sendGroupMessage(group, MessageChain.create(Plain(f'冷却中，剩余{remaining_time}秒，请稍后再试')))
        return
    img = await func[split_message[0][1:]](target)

    if isinstance(img, bytes):
        await app.sendGroupMessage(group, MessageChain.create(Image(data_bytes=img)))
    elif isinstance(img, Path | str):
        await app.sendGroupMessage(group, MessageChain.create(Image(path=img)))
