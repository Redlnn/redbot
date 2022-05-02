#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from asyncio.exceptions import TimeoutError
from typing import Literal
from uuid import UUID

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain
from loguru import logger
from sqlalchemy import update

from util.database import Database

from ..model import PlayerInfo
from ..rcon import execute_command
from ..utils import get_mc_id, get_uuid
from .query import query_uuid_by_qq, query_whitelist_by_uuid


async def del_whitelist_from_server(mc_uuid: str | UUID) -> Literal[True] | MessageChain:
    try:
        mc_id = await get_mc_id(mc_uuid)
    except TimeoutError as e:
        logger.error(f'无法查询【{mc_uuid}】对应的正版id')
        logger.exception(e)
        return MessageChain.create(Plain(f'无法查询【{mc_uuid}】对应的正版id: 👇\n{e}'))
    if not isinstance(mc_id, str):
        return MessageChain.create(Plain(f'向 mojang 查询【{mc_uuid}】的 uuid 时获得意外内容:  👇\n{await mc_id.text()}'))
    else:
        try:
            result = await execute_command(f'whitelist remove {mc_id}')
        except TimeoutError:
            return MessageChain.create(Plain(f'连接服务器超时'))
        except ValueError as e:
            logger.exception(e)
            return MessageChain.create(Plain(f'无法连接至服务器：{e}'))
        if result.startswith('Removed '):
            return True
        else:
            return MessageChain.create(Plain(f'从服务器删除id为【{mc_id}】的白名单时，服务器返回意料之外的内容：👇\n{result}'))


async def del_whitelist_by_qq(qq: int) -> MessageChain:
    player = await query_uuid_by_qq(qq)
    if player is None:
        return MessageChain.create(At(qq), Plain(f' 好像一个白名单都没有呢~'))

    await Database.exec(
        update(PlayerInfo)
        .where(PlayerInfo.qq == str(qq))
        .values(uuid1=None, uuid1_add_time=None, uuid2=None, uuid2_add_time=None)
    )
    flag1 = flag2 = False
    if player.uuid1:
        flag1 = await del_whitelist_from_server(player.uuid1)
    if player.uuid2:
        flag2 = await del_whitelist_from_server(player.uuid2)
    if flag1 is True and isinstance(flag2, MessageChain):
        return MessageChain.create(Plain('只从服务器上删除了 '), At(qq), Plain(f' 的部分白名单 👇\n')) + flag2
    elif flag2 is True and isinstance(flag1, MessageChain):
        return MessageChain.create(Plain('只从服务器上删除了 '), At(qq), Plain(f' 的部分白名单 👇\n')) + flag1
    elif isinstance(flag1, MessageChain) and isinstance(flag2, MessageChain):
        return (
            MessageChain.create(Plain('从服务器上删除 '), At(qq), Plain(f' 的白名单时失败 👇\n\n'))
            + flag1
            + MessageChain.create('\n')
            + flag2
        )
    else:
        return MessageChain.create(At(qq), Plain(f' 的白名单都删掉啦~'))


async def del_whitelist_by_id(mc_id: str) -> MessageChain:
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
    return await del_whitelist_by_uuid(mc_uuid)


async def del_whitelist_by_uuid(mc_uuid: str) -> MessageChain:
    player = await query_whitelist_by_uuid(mc_uuid)
    if player is None:
        return MessageChain.create(Plain('没有使用这个 uuid 的玩家'))
    if str(player.uuid1).replace('-', '') == mc_uuid.replace('-', ''):
        await Database.exec(
            update(PlayerInfo).where(PlayerInfo.qq == player.qq).values(uuid1=None, uuid1_add_time=None)
        )
        del_result = await del_whitelist_from_server(mc_uuid)
        if del_result is True:
            return MessageChain.create(Plain('已从服务器删除 '), At(int(player.qq)), Plain(f' 的 uuid 为 {mc_uuid} 的白名单'))
        else:
            return del_result
    elif str(player.uuid2).replace('-', '') == mc_uuid.replace('-', ''):
        await Database.exec(
            update(PlayerInfo).where(PlayerInfo.qq == player.qq).values(uuid2=None, uuid2_add_time=None)
        )
        del_result = await del_whitelist_from_server(mc_uuid)
        if del_result is True:
            return MessageChain.create(Plain('已从服务器删除 '), At(int(player.qq)), Plain(f' 的 uuid 为 {mc_uuid} 的白名单'))
        else:
            return del_result
    else:
        return MessageChain.create('发生了异常的内部逻辑错误，请联系管理员')
