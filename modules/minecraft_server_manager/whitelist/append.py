#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from asyncio.exceptions import TimeoutError
from uuid import UUID

from graia.ariadne import get_running
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain
from graia.ariadne.model import Member
from loguru import logger
from sqlalchemy import update

from util.database import Database

from ..config import config
from ..model import PlayerInfo
from ..rcon import execute_command
from ..utils import get_uuid
from .query import query_uuid_by_qq, query_whitelist_by_uuid


async def add_whitelist_to_qq(qq: int, mc_id: str, admin: bool) -> MessageChain:
    try:
        real_mc_id, mc_uuid = await get_uuid(mc_id)
    except TimeoutError as e:
        logger.error(f'向 mojang 查询【{mc_id}】的 uuid 时发生了意料之外的错误')
        logger.exception(e)
        return MessageChain.create(Plain(f'向 mojang 查询【{mc_id}】的 uuid 时发生了意料之外的错误:  👇\n{e}'))
    if not isinstance(real_mc_id, str):
        if real_mc_id.status == 204:
            return MessageChain.create(Plain('你选择的不是一个正版ID'))
        else:
            return MessageChain.create(Plain(f'向 mojang 查询【{mc_id}】的 uuid 时获得意外内容:  👇\n{await real_mc_id.text()}'))

    player = await query_whitelist_by_uuid(mc_uuid)
    if player is None:
        pass
    elif int(player.qq) == qq:
        return MessageChain.create(Plain('这个id本来就是你哒'))
    else:
        return MessageChain.create(
            Plain('你想要这个吗？\n这个是 '),
            At(int(player.qq)),
            Plain(f' 哒~'),
        )

    player = await query_uuid_by_qq(qq)
    if player is None:
        app = get_running(Ariadne)
        member: Member = await app.getMember(config.serverGroup, qq)
        player = PlayerInfo(qq=str(member.id), join_time=member.joinTimestamp)
        await Database.add(player)
    elif player.blocked:
        return MessageChain.create(Plain(f'你的账号已被封禁，封禁原因：{player.block_reason}'))

    if player.uuid1 is None and player.uuid2 is None:
        await Database.exec(
            update(PlayerInfo)
            .where(PlayerInfo.qq == str(qq))
            .values(uuid1=UUID(mc_uuid).hex, uuid1_add_time=int(time.time()))
        )
    elif player.uuid1 is not None and player.uuid2 is None:
        if admin:
            await Database.exec(
                update(PlayerInfo)
                .where(PlayerInfo.qq == str(qq))
                .values(uuid2=UUID(mc_uuid).hex, uuid2_add_time=int(time.time()))
            )
        else:
            return MessageChain.create(
                Plain('你已有一个白名单，如要申请第二个白名单请联系管理员'),
            )
    elif player.uuid2 is not None and player.uuid1 is None:
        if admin:
            await Database.exec(
                update(PlayerInfo)
                .where(PlayerInfo.qq == str(qq))
                .values(uuid1=UUID(mc_uuid).hex, uuid1_add_time=int(time.time()))
            )
        else:
            return MessageChain.create(
                Plain('你已有一个白名单，如要申请第二个白名单请联系管理员'),
            )
    else:
        if admin:
            return MessageChain.create(
                Plain('目标玩家已有两个白名单，如需添加白名单请删除至少一个'),
            )
        else:
            return MessageChain.create(
                Plain('你已经有两个白名单了噢'),
            )

    try:
        res: str = await execute_command(f'whitelist add {real_mc_id}')
    except TimeoutError:
        return MessageChain.create(Plain('添加白名单时已写入数据库，但连接服务器超时，请联系管理解决'))
    except ValueError as e:
        logger.exception(e)
        return MessageChain.create(Plain(f'添加白名单时已写入数据库但无法连接到服务器，请联系管理解决: 👇\n{e}'))

    if res.startswith('Added'):
        return MessageChain.create(At(qq), Plain(' 呐呐呐，白名单给你!'))
    else:
        return MessageChain.create(Plain(f'添加白名单时已写入数据库但服务器返回预料之外的内容: 👇\n{res}'))
