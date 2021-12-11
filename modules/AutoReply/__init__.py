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
# type | group_id | keyword | value

from pathlib import Path

import regex as re
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.model import Group
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from utils.Limit.Blacklist import group_blacklist
from utils.ModuleRegister import Module
from utils.TextWithImg2Img import async_generate_img

saya = Saya.current()
channel = Channel.current()

if Path.exists(Path(Path(__file__).parent, 'config.py')):
    from .config import disabled, fuzzy_reply, re_reply, reply  # noqa
else:
    from .config_exp import disabled, fuzzy_reply, re_reply, reply

Module(
    name='自动回复',
    config_name='AutoReply',
    file_name=str(Path(__file__).parent),
    author=['Red_lnn'],
    description='支持全文匹配、正则匹配、模糊匹配，若回复内容中包含的文字字符数大于100字，则会将内容转为图片发送',
    can_disable=False,
).register()


@channel.use(ListenerSchema(listening_events=[GroupMessage], decorators=[group_blacklist()]))
async def main(app: Ariadne, group: Group, message: MessageChain):
    if disabled:
        saya.uninstall_channel(channel)
        return
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
        if isinstance(_reply, str):
            chain.append(Plain(_))
        elif isinstance(_reply, bytes):
            chain.append(Image(data_bytes=_))
    if chain != MessageChain([]):
        if chain.count(Plain) > 0:
            if len(chain.include(Plain).asDisplay()) > 100:
                img_bytes = await async_generate_img(reply[group.id][msg])
                await app.sendGroupMessage(
                    group,
                    MessageChain.create(Image(data_bytes=(img_bytes))),
                )
                return
        await app.sendGroupMessage(group, chain)


async def re_match(msg: str, app: Ariadne, group: Group):
    for _ in re_reply[group.id].keys():
        if re.search(_, msg):
            continue
        chain = MessageChain.create()
        for i in re_reply[group.id][_]:
            _reply = type(i)
            if isinstance(_reply, str):
                chain.append(Plain(i))
            elif isinstance(_reply, bytes):
                chain.append(Image(data_bytes=i))
        if chain != MessageChain([]):
            if chain.count(Plain) > 0:
                if len(chain.include(Plain).asDisplay()) > 100:
                    img_bytes = await async_generate_img(reply[group.id][msg])
                    await app.sendGroupMessage(
                        group,
                        MessageChain.create(Image(data_bytes=(img_bytes))),
                    )
                    continue
            await app.sendGroupMessage(group, chain)


async def fuzzy_match(msg: str, app: Ariadne, group: Group):
    for _ in fuzzy_reply[group.id].keys():
        if _ not in msg:
            continue
        chain = MessageChain.create()
        for i in fuzzy_reply[group.id][_]:
            _reply = type(i)
            if isinstance(_reply, str):
                chain.append(Plain(i))
            elif isinstance(_reply, bytes):
                chain.append(Image(data_bytes=i))
        if chain != MessageChain([]):
            if chain.count(Plain) > 0:
                if len(chain.include(Plain).asDisplay()) > 100:
                    img_bytes = await async_generate_img(reply[group.id][msg])
                    await app.sendGroupMessage(
                        group,
                        MessageChain.create(Image(data_bytes=(img_bytes))),
                    )
                    continue
            await app.sendGroupMessage(group, chain)
