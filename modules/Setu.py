#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
from datetime import datetime

import aiohttp
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Forward, ForwardNode, Image, Plain
from graia.ariadne.message.parser.twilight import (
    FullMatch,
    RegexMatch,
    Sparkle,
    Twilight,
    WildcardMatch,
)
from graia.ariadne.model import Group, Member
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from config import config_data
from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Rate import MemberInterval
from utils.ModuleRegister import Module

saya = Saya.current()
channel = Channel.current()

Module(
    name='涩图（不可以色色o）',
    config_name='Setu',
    file_name=os.path.basename(__file__),
    author=['Red_lnn', 'A60(djkcyl)'],
    description='提供白名单管理、在线列表查询、服务器命令执行功能',
    usage=' - [!！.]涩图 —— 获取随机涩图\n' ' - [!！.]{关键词}涩图 —— 获取指定关键词的涩图',
).register()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                Sparkle(
                    [RegexMatch(r'[.!！]')],
                    {"tag": WildcardMatch(optional=True), "header": FullMatch("涩图")},
                ),
            )
        ],
        decorators=[group_blacklist(), MemberInterval.require(30)],
    )
)
async def main(app: Ariadne, group: Group, member: Member, tag: WildcardMatch):
    if not config_data['Modules']['Setu']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['Setu']['DisabledGroup']:
        if group.id in config_data['Modules']['Setu']['DisabledGroup']:
            return

    async with aiohttp.ClientSession('http://a60.one:404') as session:
        if tag.matched:
            target_tag = tag.result.getFirst(Plain).text
            async with session.get(f'/get/tags/{target_tag}?san=2') as resp:
                if resp.status in (200, 404):
                    res: dict = await resp.json()
                else:
                    res = {'code': 500}
        else:
            async with session.get('/?san=2') as resp:
                if resp.status == 200:
                    res: dict = await resp.json()
                else:
                    res = {'code': 500}
    if res.get('code', False) == 404 and tag.matched:
        await app.sendGroupMessage(group, MessageChain.create(Plain('未找到相应tag的色图')))
    elif res.get('code', False) == 200:
        forward_nodes = [
            ForwardNode(
                senderId=member.id,
                time=datetime.now(),
                senderName=member.name,
                messageChain=MessageChain.create('你好，刚刚的我，我给你发涩图来了~'),
            ),
            ForwardNode(
                senderId=member.id,
                time=datetime.now(),
                senderName=member.name,
                messageChain=MessageChain.create('请米娜桑坐稳扶好，涩图要来咯~诶嘿嘿嘿嘿~'),
            ),
            ForwardNode(
                senderId=member.id,
                time=datetime.now(),
                senderName=member.name,
                messageChain=MessageChain.create(
                    Plain(
                        f'pixiv id：{res["data"]["imgs"][0]["pic"]}\n'
                        f'作品名称：{res["data"]["imgs"][0]["name"]}\n'
                        f'涩气值: {res["data"]["imgs"][0]["sanity_level"]}'
                    ),
                ),
            ),
            ForwardNode(
                senderId=member.id,
                time=datetime.now(),
                senderName=member.name,
                messageChain=MessageChain.create(
                    Image(url=res['data']['imgs'][0]['url']),
                ),
            ),
            ForwardNode(
                senderId=member.id,
                time=datetime.now(),
                senderName=member.name,
                messageChain=MessageChain.create(
                    Plain('看够了吗？看够了就没了噢~'),
                ),
            ),
        ]
        message = MessageChain.create(Forward(nodeList=forward_nodes))
        msg_id = await app.sendGroupMessage(group, message)
        await asyncio.sleep(60)
        try:
            await app.recallMessage(msg_id)
        except Exception:
            pass
    else:
        await app.sendGroupMessage(group, MessageChain.create(Plain('慢一点慢一点，别冲辣！')))
