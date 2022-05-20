#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from os.path import basename, dirname, join
from pathlib import Path
from random import choices, randint

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Plain, Source
from graia.ariadne.message.parser.twilight import (
    RegexMatch,
    RegexResult,
    SpacePolicy,
    Twilight,
    WildcardMatch,
)
from graia.ariadne.model import Group, Member
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from sqlalchemy import select

from util.control import DisableModule
from util.control.permission import GroupPermission
from util.database import Database
from util.database.models import UserInfo
from util.module_register import Module
from util.path import root_path

from .util import Reward, get_signin_img

channel = Channel.current()
module_name = basename(__file__)[:-3]

Module(
    name='签到',
    file_name=module_name,
    author=['Red_lnn'],
).register()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]?签到').space(SpacePolicy.NOSPACE)])],
        decorators=[GroupPermission.require(), DisableModule.require(module_name)],
    )
)
async def signin(app: Ariadne, group: Group, member: Member, source: Source):
    font_path = Path(root_path, 'fonts', 'OPPOSans-B.ttf')
    result = await Database.select_first(select(UserInfo).where(UserInfo.qq == member.id))
    if result is None or result[0] is None:
        user: UserInfo = UserInfo(qq=str(member.id))
    else:
        user: UserInfo = result[0]

    # 判断时间戳是不是今天
    if time.localtime(user.last_signin_time).tm_yday == time.localtime().tm_yday:
        await app.sendMessage(group, MessageChain.create(Plain('你今天已经签到过了哦~')), quote=source)

        return

    user.total_signin_days += 1

    if user.total_signin_days <= 1 or time.time() - user.last_signin_time > 86400:
        is_signin_consecutively = False
        user.consecutive_signin_days = 0
    else:
        is_signin_consecutively = True
        user.consecutive_signin_days += 1

    added_coin = randint(3, 8)
    added_gold = choices([1, 2, 3], weights=[89, 10, 1])[0]
    added_exp = randint(2, 10)

    user.coin += added_coin
    user.gold += added_gold
    user.exp += added_exp
    user.last_signin_time = int(time.time())

    if not await Database.update_exist(user):
        await app.sendMessage(group, MessageChain.create(Plain('签到数据保存失败，请联系 Bot 主人')))
        return

    # Lv1 <500
    # Lv2 <1500
    # Lv3 <3000
    # Lv4 <5000
    # Lv5 <7500
    # Lv6 <10500
    levels = {
        0: 0,
        1: 500,
        2: 1500,
        3: 3000,
        4: 5000,
        5: 7500,
        6: 10500,
        7: 10500,
    }
    if user.exp >= 10500:
        level = 6
    elif user.exp >= 7500:
        level = 5
    elif user.exp >= 5000:
        level = 4
    elif user.exp >= 3000:
        level = 3
    elif user.exp >= 1500:
        level = 2
    elif user.exp >= 500:
        level = 1
    else:
        level = 0

    img_bytes = await get_signin_img(
        qq=member.id,
        name=member.name,
        level=level,
        exp=(user.exp - levels[level], levels[level + 1]),
        total_days=user.total_signin_days,
        consecutive_days=user.consecutive_signin_days,
        is_signin_consecutively=is_signin_consecutively,
        rewards=[
            Reward(name='经验', num=added_exp),
            Reward(num=added_coin, ico=join(dirname(__file__), 'imgs', '原石.png')),
            Reward(num=added_gold, ico=join(dirname(__file__), 'imgs', '纠缠之缘.png')),
        ],
        font_path=str(font_path),
    )

    await app.sendMessage(group, MessageChain.create(Image(data_bytes=img_bytes)))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([RegexMatch(r'[!！.]清除签到信息').space(SpacePolicy.FORCE), 'target' @ WildcardMatch()])
        ],
        decorators=[GroupPermission.require(GroupPermission.BOT_ADMIN), DisableModule.require(module_name)],
    )
)
async def clear(app: Ariadne, group: Group, target: RegexResult):
    msg: MessageChain = target.result  # type: ignore
    if msg.onlyContains(At):
        result = await clear_signin(str(msg.getFirst(At).target))
    elif msg.onlyContains(Plain) and msg.asDisplay().strip().isdigit():
        result = await clear_signin(msg.asDisplay().strip())
    else:
        await app.sendMessage(group, MessageChain.create(Plain('参数错误，请输入正确的QQ号或者@某人')))
        return
    await app.sendMessage(group, MessageChain.create(Plain('Success!' if result else 'Failed!')))


async def clear_signin(qq: str):
    result = await Database.select_first(select(UserInfo).where(UserInfo.qq == qq))
    if result is None or result[0] is None:
        return True
    return await Database.delete_exist(result[0])
