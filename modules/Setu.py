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
    ArgumentMatch,
    FullMatch,
    RegexMatch,
    Sparkle,
    Twilight,
    WildcardMatch,
)
from graia.ariadne.model import Group, Member, MemberPerm
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from config import config_data
from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Interval import MemberInterval
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
                    {
                        'tag': WildcardMatch(optional=True),
                        'header': FullMatch('涩图'),
                        'san': ArgumentMatch('--san', '-S', default='2', regex=r'2|4|6', help='最高涩气值，可为2|4|6'),
                        'num': ArgumentMatch('--num', '-N', default='1', regex=r'[1-5]', help='涩图数量'),
                    },
                ),
            )
        ],
        decorators=[group_blacklist(), MemberInterval.require(30)],
    )
)
async def main(app: Ariadne, group: Group, member: Member, tag: WildcardMatch, san: ArgumentMatch, num: ArgumentMatch):
    if not config_data['Modules']['Setu']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['Setu']['DisabledGroup']:
        if group.id in config_data['Modules']['Setu']['DisabledGroup']:
            return

    if int(san.result.asDisplay()) >= 4 and not (
        member.permission in (MemberPerm.Administrator, MemberPerm.Owner)
        or member.id in config_data['Basic']['Permission']['Admin']
    ):
        await app.sendGroupMessage(group, MessageChain.create(Plain('你没有权限使用 san 参数')))
        return
    async with aiohttp.ClientSession('http://a60.one:404') as session:
        if tag.matched:
            target_tag = tag.result.getFirst(Plain).text
            async with session.get(
                f'/get/tags/{target_tag}?san={san.result.asDisplay()}&num={num.result.asDisplay()}'
            ) as resp:
                if resp.status in (200, 404):
                    res: dict = await resp.json()
                else:
                    res = {'code': 500}
        else:
            async with session.get(f'/?san={san.result.asDisplay()}&num={num.result.asDisplay()}') as resp:
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
                messageChain=MessageChain.create('我有涩图要给大伙康康，请米娜桑坐稳扶好哦嘿嘿嘿~'),
            ),
        ]
        for img in res['data']['imgs']:
            forward_nodes.extend(
                [
                    ForwardNode(
                        senderId=member.id,
                        time=datetime.now(),
                        senderName=member.name,
                        messageChain=MessageChain.create(
                            Plain(
                                f'作品名称：{img["name"]}\n'
                                f'pixiv id：{img["pic"]}\n'
                                f'涩气值: {img["sanity_level"]}\n'
                                f'作者昵称：{img["username"]}\n'
                                f'作者 id：{img["userid"]}\n'
                                f'关键词：{img["tags"]}'
                            ),
                        ),
                    ),
                    ForwardNode(
                        senderId=member.id,
                        time=datetime.now(),
                        senderName=member.name,
                        messageChain=MessageChain.create(
                            Image(url=img['url']),
                        ),
                    ),
                ]
            )
        forward_nodes.append(
            ForwardNode(
                senderId=member.id,
                time=datetime.now(),
                senderName=member.name,
                messageChain=MessageChain.create(
                    Plain('看够了吗？看够了就没了噢~'),
                ),
            ),
        )
        message = MessageChain.create(Forward(nodeList=forward_nodes))
        msg_id = await app.sendGroupMessage(group, message)
        await asyncio.sleep(40)
        try:
            await app.recallMessage(msg_id)
        except Exception:
            pass
    else:
        await app.sendGroupMessage(group, MessageChain.create(Plain('慢一点慢一点，别冲辣！')))
