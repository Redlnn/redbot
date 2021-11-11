#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import regex
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Quote
from graia.ariadne.model import Group, MemberPerm
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Permission import Permission

saya = Saya.current()
channel = Channel.current()

channel.name('读取/发送消息的可持久化字符串')
channel.author('Red_lnn')
channel.description(
        '用法：\n'
        ' - 回复需要读取的消息并且回复内容只含有“[!！.]读取消息”获得消息的可持久化字符串\n'
        ' - [!！.]发送消息 <可持久化字符串> —— 用于从可持久化字符串发送消息'
)

# 生效的群组，若为空，即()，则在所有群组生效
# 格式为：active_group = (123456, 456789, 789012)
active_group = ()


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                decorators=[group_blacklist(), Permission.group_perm_check(MemberPerm.Administrator)],
        )
)
async def main(app: Ariadne, group: Group, message: MessageChain):
    if group.id not in active_group and active_group:
        return
    if regex.match(r'^[!！.]读取消息$', message.asDisplay()):
        try:
            quote_id = message.include(Quote).getFirst(Quote).id
        except IndexError:
            return
        try:
            message_event = await app.getMessageFromId(quote_id)
        except UnknownTarget:
            await app.sendGroupMessage(group, MessageChain.create(Plain('找不到该消息，对象不存在')))
            return
        chain = message_event.messageChain
        await app.sendGroupMessage(
                group, MessageChain.create(Plain(f'消息ID: {quote_id}\n消息内容：{chain.asPersistentString()}'))
        )
    elif regex.match(r'^[!！.]发送消息\ .+', message.asDisplay()):
        msg = regex.sub(r'[!！.]发送消息\ ', '', message.asDisplay(), count=1)
        if msg:
            await app.sendGroupMessage(group, MessageChain.fromPersistentString(msg))
