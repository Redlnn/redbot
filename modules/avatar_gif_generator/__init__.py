#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Plain
from graia.ariadne.model import Group, Member
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from util.control import require_disable
from util.control.interval import ManualInterval
from util.control.permission import GroupPermission

from .ding import ding

channel = Channel.current()

channel.meta['name'] = '用你的头像生成点啥'
channel.meta['author'] = ['Red_lnn', 'SereinFish']
channel.meta['description'] = '用你的头像生成一些有趣的图片\n用法：\n  [!！.]顶 At/QQ号 —— 让猫猫虫咖波顶着你的头像耍'

func = {
    '顶': ding,
}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], decorators=[GroupPermission.require(), require_disable(channel.module)]
    )
)
async def main(app: Ariadne, group: Group, member: Member, message: MessageChain):
    if not message.has(Plain):
        return
    elif message.display[0] not in {'!', '！', '.'}:
        return

    split_message = message.display.strip().split(' ')
    if len(split_message) != 2:
        return
    elif split_message[0][1:] not in func:
        return

    if message.has(At):
        target = message.get_first(At).target
    elif split_message[1].isdigit():
        target = split_message[1]
    else:
        return

    rate_limit, remaining_time = ManualInterval.require(f'AvatarImgGen_{member.id}', 30, 1)
    if not rate_limit:
        await app.send_message(group, MessageChain(Plain(f'冷却中，剩余{remaining_time}秒，请稍后再试')))
        return
    img = await func[split_message[0][1:]](target)

    if isinstance(img, bytes):
        await app.send_message(group, MessageChain(Image(data_bytes=img)))
    elif isinstance(img, Path | str):
        await app.send_message(group, MessageChain(Image(path=img)))
