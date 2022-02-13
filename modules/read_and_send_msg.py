#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import basename

import regex as re
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Quote
from graia.ariadne.model import Group, MemberPerm
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from util.control import DisableModule
from util.control.permission import GroupPermission
from util.module_register import Module

channel = Channel.current()
module_name = basename(__file__)[:-3]

Module(
    name='读取/发送消息的可持久化字符串',
    file_name=module_name,
    author=['Red_lnn'],
    description='获得一个随机数',
    usage='仅限群管理员使用\n - 回复需要读取的消息并且回复内容只含有“[!！.]读取消息”获得消息的可持久化字符串\n - [!！.]发送消息 <可持久化字符串> —— 用于从可持久化字符串发送消息',
).register()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        decorators=[
            GroupPermission.require(MemberPerm.Administrator, send_alert=False),
            DisableModule.require(module_name),
        ],
    )
)
async def main(app: Ariadne, group: Group, message: MessageChain):
    if re.match(r'^[!！.]读取消息$', message.asDisplay()):
        try:
            quote_id = message.include(Quote).getFirst(Quote).id
        except IndexError:
            return
        try:
            message_event = await app.getMessageFromId(quote_id)
        except UnknownTarget:
            await app.sendMessage(group, MessageChain.create(Plain('找不到该消息，对象不存在')))
            return
        chain = message_event.messageChain
        await app.sendMessage(group, MessageChain.create(Plain(f'消息ID: {quote_id}\n消息内容：{chain.asPersistentString()}')))
    elif re.match(r'^[!！.]发送消息\ .+', message.asDisplay()):
        msg = re.sub(r'[!！.]发送消息\ ', '', message.asDisplay(), count=1)
        if msg:
            await app.sendMessage(group, MessageChain.fromPersistentString(msg))
