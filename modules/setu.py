#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
该模块使用的不是 Lolicon API
"""

import asyncio
import contextlib
from datetime import datetime
from typing import Any

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
    SpacePolicy,
    Twilight,
    WildcardMatch,
)
from graia.ariadne.model import Group, Member, MemberPerm
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from pydantic import AnyHttpUrl

from util import GetAiohttpSession
from util.config import RConfig, basic_cfg
from util.control import require_disable
from util.control.interval import MemberInterval
from util.control.permission import GroupPermission

channel = Channel.current()

channel.meta['name'] = '涩图（不可以色色o）'
channel.meta['author'] = ['Red_lnn', 'A60(djkcyl)']
channel.meta['description'] = '提供白名单管理、在线列表查询、服务器命令执行功能\n用法：\n - [!！.]涩图 —— 获取随机涩图\n - [!！.]{关键词}涩图 —— 获取指定关键词的涩图'


class Setu(RConfig):
    __filename__: str = 'setu'
    apiUrl: AnyHttpUrl = 'http://localhost:8080'  # type: ignore


setu_config = Setu()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                RegexMatch(r'[.!！]'),
                'tag' @ WildcardMatch(optional=True).space(SpacePolicy.NOSPACE),
                'header' @ FullMatch('涩图'),
                'san' @ ArgumentMatch('--san', '-S', type=int, default=2, choices=[2, 4, 6]),  # 最高涩气值，可为2|4|6'
                'num' @ ArgumentMatch('--num', '-N', type=int, default=1, choices=[1, 2, 3, 4, 5]),  # 涩图数量
            )
        ],
        decorators=[GroupPermission.require(), MemberInterval.require(30), require_disable(channel.module)],
    )
)
async def main(
    app: Ariadne,
    group: Group,
    member: Member,
    tag: RegexResult,
    san: ArgResult[int],
    num: ArgResult[int],
):
    if san.result is None:
        return
    if int(san.result) >= 4 and not (
        member.permission in {MemberPerm.Administrator, MemberPerm.Owner} or member.id in basic_cfg.admin.admins
    ):
        await app.send_message(group, MessageChain(Plain('你没有权限使用 san 参数')))
        return
    session = GetAiohttpSession.get_session()
    if tag.matched and tag.result is not None:
        target_tag = tag.result.get_first(Plain).text
        async with session.get(f'{setu_config.apiUrl}/get/tags/{target_tag}?san={san.result}&num={num.result}') as resp:
            res: dict[str, Any] = await resp.json() if resp.status in {200, 404} else {'code': 500}
    else:
        async with session.get(f'{setu_config.apiUrl}/?san={san.result}&num={num.result}') as resp:
            res: dict[str, Any] = await resp.json() if resp.status == 200 else {'code': 500}
    if res.get('code') == 404 and tag.matched:
        await app.send_message(group, MessageChain(Plain('未找到相应tag的色图')))
    elif res.get('code') == 200:
        forward_nodes = [
            ForwardNode(target=member, time=datetime.now(), message=MessageChain('我有涩图要给大伙康康，请米娜桑坐稳扶好哦嘿嘿嘿~')),
        ]
        for img in res['data']['imgs']:
            forward_nodes.extend(
                [
                    ForwardNode(
                        target=member,
                        time=datetime.now(),
                        message=MessageChain(
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
                    ForwardNode(target=member, time=datetime.now(), message=MessageChain(Image(url=img['url']))),
                ]
            )
        forward_nodes.append(
            ForwardNode(target=member, time=datetime.now(), message=MessageChain(Plain('看够了吗？看够了就没了噢~'))),
        )
        message = MessageChain(Forward(nodeList=forward_nodes))
        msg_id = await app.send_message(group, message)
        await asyncio.sleep(40)
        with contextlib.suppress(UnknownTarget):
            await app.recall_message(msg_id)
    else:
        await app.send_message(group, MessageChain(Plain('慢一点慢一点，别冲辣！')))
