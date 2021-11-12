#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动回复

支持全文匹配、正则匹配、模糊匹配

若回复内容中包含的文字字符数大于100字，则会将内容转为图片发送
"""

# TODO: 将自动回复关键词和内容写入数据库，并支持群管理在群内修改。每次启动时从数据库读出作为缓存，新增时同时写入数据库和缓存
# 数据库结构：
# AutoReply表
# type | group | key | value

import os.path
from io import BytesIO

import regex
from graia.ariadne.app import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.model import Group
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Rate import MemberInterval
from utils.TextWithImg2Img import async_generate_img

saya = Saya.current()
channel = Channel.current()

if os.path.exists(os.path.join(os.path.dirname(__file__), 'config.py')):
    from .config import disabled, reply, re_reply, fuzzy_reply  # noqa
else:
    from .config_exp import disabled, reply, re_reply, fuzzy_reply

if disabled:
    saya.uninstall_channel(channel)

channel.name('自动回复')
channel.author('Red_lnn')
channel.description('支持全文匹配、正则匹配、模糊匹配，若回复内容中包含的文字字符数大于100字，则会将内容转为图片发送')


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                decorators=[group_blacklist(), MemberInterval.require(1, send_alert=False)]
        )
)
async def main(app: Ariadne, group: Group, message: MessageChain):
    msg: str = message.asDisplay().strip()
    if not msg:
        return
    if group.id in reply.keys():
        await full_match(msg, app, group)
    if group.id in re_reply.keys():
        await re_match(msg, app, group)
    if group.id in fuzzy_reply.keys():
        await fuzzy_match(msg, app, group)


async def full_match(msg: str, app: Ariadne, group: Group):
    if msg not in reply[group.id].keys():
        return
    chain = MessageChain.create()
    for _ in reply[group.id][msg]:
        _reply = type(_)
        if _reply is str:
            chain.append(Plain(_))
        elif _reply is BytesIO:
            chain.append(Image(data_bytes=_))
    if chain != MessageChain([]):
        if chain.count(Plain) > 0:
            if len(chain.include(Plain).asDisplay()) > 100:
                await app.sendGroupMessage(
                        group,
                        MessageChain.create(
                                Image(data_bytes=(await async_generate_img(reply[group.id][msg])).getvalue())
                        ),
                )
                return
        await app.sendGroupMessage(group, chain)


async def re_match(msg: str, app: Ariadne, group: Group):
    for _ in re_reply[group.id].keys():
        if regex.search(_, msg):
            continue
        chain = MessageChain.create()
        for i in re_reply[group.id][_]:
            _reply = type(i)
            if _reply is str:
                chain.append(Plain(i))
            elif _reply is BytesIO:
                chain.append(Image(data_bytes=i))
        if chain != MessageChain([]):
            if chain.count(Plain) > 0:
                if len(chain.include(Plain).asDisplay()) > 100:
                    await app.sendGroupMessage(
                            group,
                            MessageChain.create(
                                    Image(data_bytes=(await async_generate_img(reply[group.id][msg])).getvalue())
                            ),
                    )
                    continue
            await app.sendGroupMessage(group, chain)


async def fuzzy_match(msg: str, app: Ariadne, group: Group):
    for _ in fuzzy_reply[group.id].keys():
        if msg not in _:
            continue
        chain = MessageChain.create()
        for i in fuzzy_reply[group.id][_]:
            _reply = type(i)
            if _reply is str:
                chain.append(Plain(i))
            elif _reply is BytesIO:
                chain.append(Image(data_bytes=i))
        if chain != MessageChain([]):
            if chain.count(Plain) > 0:
                if len(chain.include(Plain).asDisplay()) > 100:
                    await app.sendGroupMessage(
                            group,
                            MessageChain.create(
                                    Image(data_bytes=(await async_generate_img(reply[group.id][msg])).getvalue())
                            ),
                    )
                    continue
            await app.sendGroupMessage(group, chain)
