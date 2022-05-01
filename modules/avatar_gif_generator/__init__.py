#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import dirname, split
from pathlib import Path

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Plain
from graia.ariadne.model import Group, Member
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from util.control import DisableModule
from util.control.interval import ManualInterval
from util.control.permission import GroupPermission
from util.module_register import Module

from .ding import ding

channel = Channel.current()

module_name = split(dirname(__file__))[-1]

Module(
    name='用你的头像生成点啥',
    file_name=module_name,
    author=['Red_lnn', 'SereinFish'],
    description='用你的头像生成一些有趣的图片',
    usage='[!！.]顶 At/QQ号 —— 让猫猫虫咖波顶着你的头像耍',
    can_disable=False,
).register()

func = {
    '顶': ding,
}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], decorators=[GroupPermission.require(), DisableModule.require(module_name)]
    )
)
async def main(app: Ariadne, group: Group, member: Member, message: MessageChain):
    if not message.has(Plain):
        return
    elif message.asDisplay()[0] not in ('!', '！', '.'):
        return

    split_message = message.asDisplay().strip().split(' ')
    if len(split_message) != 2:
        return
    elif split_message[0][1:] not in func:
        return

    if message.has(At):
        target = message.getFirst(At).target
    elif split_message[1].isdigit():
        target = split_message[1]
    else:
        return

    rate_limit, remaining_time = ManualInterval.require(f'AvatarImgGen_{member.id}', 30, 1)
    if not rate_limit:
        await app.sendMessage(group, MessageChain.create(Plain(f'冷却中，剩余{remaining_time}秒，请稍后再试')))
        return
    img = await func[split_message[0][1:]](target)

    if isinstance(img, bytes):
        await app.sendMessage(group, MessageChain.create(Image(data_bytes=img)))
    elif isinstance(img, Path | str):
        await app.sendMessage(group, MessageChain.create(Image(path=img)))
