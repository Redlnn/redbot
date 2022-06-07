#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Quote
from graia.ariadne.model import Group, MemberPerm
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from util.control import require_disable
from util.control.permission import GroupPermission

channel = Channel.current()

channel.meta['name'] = '读取/发送消息的可持久化字符串'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = '仅限群管理员使用\n'
' - 回复需要读取的消息并且回复内容只含有“[!！.]读取消息”获得消息的可持久化字符串\n'
' - [!！.]发送消息 <可持久化字符串> —— 用于从可持久化字符串发送消息'


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        decorators=[
            GroupPermission.require(MemberPerm.Administrator, send_alert=False),
            require_disable(channel.module),
        ],
    )
)
async def main(app: Ariadne, group: Group, message: MessageChain):
    if re.match(r'^[!！.]读取消息$', message.display):
        try:
            quote_id = message.include(Quote).get_first(Quote).id
        except IndexError:
            return
        try:
            message_event = await app.get_message_from_id(quote_id)
        except UnknownTarget:
            await app.send_message(group, MessageChain(Plain('找不到该消息，对象不存在')))
            return
        chain = message_event.message_chain
        await app.send_message(group, MessageChain(Plain(f'消息ID: {quote_id}\n消息内容：{chain.as_persistent_string()}')))
    elif re.match(r'^[!！.]发送消息 .+', message.display):
        if msg := re.sub(r'[!！.]发送消息 ', '', message.display, count=1):
            await app.send_message(group, MessageChain.from_persistent_string(msg))
