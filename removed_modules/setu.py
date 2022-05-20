#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
该模块使用的不是 Lolicon API
"""

import asyncio
from datetime import datetime
from os.path import basename

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Forward, ForwardNode, Image, Plain
from graia.ariadne.message.parser.twilight import (
    ArgResult,
    ArgumentMatch,
    FullMatch,
    RegexMatch,
    RegexResult,
    Twilight,
    WildcardMatch,
)
from graia.ariadne.model import Group, Member, MemberPerm
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from pydantic import AnyHttpUrl

from util.config import RConfig, basic_cfg
from util.control import DisableModule
from util.control.interval import MemberInterval
from util.control.permission import GroupPermission
from util.get_aiohtto_session import get_session
from util.module_register import Module

channel = Channel.current()
module_name = basename(__file__)[:-3]

Module(
    name='涩图（不可以色色o）',
    file_name=module_name,
    author=['Red_lnn', 'A60(djkcyl)'],
    description='提供白名单管理、在线列表查询、服务器命令执行功能',
    usage=' - [!！.]涩图 —— 获取随机涩图\n' ' - [!！.]{关键词}涩图 —— 获取指定关键词的涩图',
).register()


class Setu(RConfig):
    __filename__: str = 'setu'
    apiUrl: AnyHttpUrl = 'http://localhost:8080'  # type: ignore


setu_config = Setu()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    RegexMatch(r'[.!！]'),
                    'tag' @ WildcardMatch(optional=True),
                    'header' @ FullMatch('涩图'),
                    'san' @ ArgumentMatch('--san', '-S', default='2', choices=['2', '4', '6']),  # 最高涩气值，可为2|4|6'
                    'num' @ ArgumentMatch('--num', '-N', default='1', choices=['1', '2', '3', '4', '5']),  # 涩图数量
                ],
            )
        ],
        decorators=[GroupPermission.require(), MemberInterval.require(30), DisableModule.require(module_name)],
    )
)
async def main(
    app: Ariadne,
    group: Group,
    member: Member,
    tag: RegexResult,
    san: ArgResult[MessageChain],
    num: ArgResult[MessageChain],
):
    if int(san.result.asDisplay()) >= 4 and not (  # type: ignore
        member.permission in (MemberPerm.Administrator, MemberPerm.Owner) or member.id in basic_cfg.admin.admins
    ):
        await app.sendMessage(group, MessageChain.create(Plain('你没有权限使用 san 参数')))
        return
    session = get_session()
    if tag.matched:
        target_tag = tag.result.getFirst(Plain).text  # type: ignore
        async with session.get(
                    f'{setu_config.apiUrl}/get/tags/{target_tag}?san={san.result.asDisplay()}&num={num.result.asDisplay()}'  # type: ignore
                ) as resp:
            res: dict = await resp.json() if resp.status in (200, 404) else {'code': 500}
    else:
        async with session.get(
                    f'{setu_config.apiUrl}/?san={san.result.asDisplay()}&num={num.result.asDisplay()}'  # type: ignore
                ) as resp:
            res = await resp.json() if resp.status == 200 else {'code': 500}
    if res.get('code') == 404 and tag.matched:
        await app.sendMessage(group, MessageChain.create(Plain('未找到相应tag的色图')))
    elif res.get('code') == 200:
        forward_nodes = [
            ForwardNode(
                senderId=member.id,
                time=datetime.now(),
                senderName=member.name,
                messageChain=MessageChain.create('我有涩图要给大伙康康，请米娜桑坐稳扶好哦嘿嘿嘿~'),
            ),
        ]
        for img in res['data']['imgs']:  # type: ignore
            forward_nodes.extend(
                [
                    ForwardNode(
                        target=member,
                        time=datetime.now(),
                        message=MessageChain.create(
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
                        target=member,
                        time=datetime.now(),
                        message=MessageChain.create(
                            Image(url=img['url']),
                        ),
                    ),
                ]
            )
        forward_nodes.append(
            ForwardNode(
                target=member,
                time=datetime.now(),
                messageChain=MessageChain.create(
                    Plain('看够了吗？看够了就没了噢~'),
                ),
            ),
        )
        message = MessageChain.create(Forward(nodeList=forward_nodes))
        msg_id = await app.sendMessage(group, message)
        await asyncio.sleep(40)
        try:
            await app.recallMessage(msg_id)  # type: ignore
        except UnknownTarget:
            pass
    else:
        await app.sendMessage(group, MessageChain.create(Plain('慢一点慢一点，别冲辣！')))
