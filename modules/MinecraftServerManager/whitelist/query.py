#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from uuid import UUID

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain

from ..config import config
from ..database import PlayersTable
from ..model import Player
from ..utils import get_mc_id, get_uuid


async def query_whitelist_by_uuid(mc_uuid: str) -> Player | None:
    query_target = UUID(mc_uuid)
    try:
        data: PlayersTable = PlayersTable.get(
            (PlayersTable.group == config.serverGroup)
            & ((PlayersTable.uuid1 == query_target) | (PlayersTable.uuid2 == query_target))
        )
    except PlayersTable.DoesNotExist:
        return None
    return Player(
        group=data.group,
        qq=data.qq,
        joinTime=data.joinTimestamp,
        leaveTime=data.leaveTimestamp,
        uuid1=data.uuid1,
        uuid1AddedTime=data.uuid1AddedTime,
        uuid2=data.uuid2,
        uuid2AddedTime=data.uuid2AddedTime,
        blocked=data.blocked,
        blockReason=data.blockReason,
    )


async def query_whitelist_by_id(mc_id: str) -> tuple[dict[str, int | str], Player | None]:
    real_mc_id, mc_uuid = await get_uuid(mc_id)
    if not isinstance(real_mc_id, str):
        if real_mc_id.status != 200:
            return {'status': 'error', 'code': real_mc_id.status, 'msg': await real_mc_id.text()}, None

    return {'status': 'success', 'code': 200, 'msg': ''}, await query_whitelist_by_uuid(mc_uuid)


async def query_uuid_by_qq(
    qq: int | str,
) -> Player | None:
    try:
        data: PlayersTable = PlayersTable.get((PlayersTable.qq == qq) & (PlayersTable.group == config.serverGroup))
    except PlayersTable.DoesNotExist:
        return None
    else:
        return Player(
            group=data.group,
            qq=data.qq,
            joinTime=data.joinTimestamp,
            leaveTime=data.leaveTimestamp,
            uuid1=data.uuid1,
            uuid1AddedTime=data.uuid1AddedTime,
            uuid2=data.uuid2,
            uuid2AddedTime=data.uuid2AddedTime,
            blocked=data.blocked,
            blockReason=data.blockReason,
        )


async def query_qq_by_uuid(mc_uuid: str) -> Player | None:
    target = UUID(mc_uuid)
    try:
        data: PlayersTable = PlayersTable.get(((PlayersTable.uuid1 == target) | (PlayersTable.uuid2 == target)) & (PlayersTable.group == config.serverGroup))
    except PlayersTable.DoesNotExist:
        return None
    else:
        return Player(
            group=data.group,
            qq=data.qq,
            joinTime=data.joinTimestamp,
            leaveTime=data.leaveTimestamp,
            uuid1=data.uuid1,
            uuid1AddedTime=data.uuid1AddedTime,
            uuid2=data.uuid2,
            uuid2AddedTime=data.uuid2AddedTime,
            blocked=data.blocked,
            blockReason=data.blockReason,
        )


async def gen_query_info_text(player: Player) -> MessageChain:
    print(player)
    if player.blocked:
        return MessageChain.create(At(player.qq), Plain(f' 已被封禁，封禁原因：{player.blockReason}'))
    if player.uuid1 is None and player.uuid2 is None:
        return MessageChain.create(At(player.qq), Plain(f' 一个白名单都没有呢'))
    info_text = f'({player.qq}) 的白名单信息如下：\n | 入群时间: {player.joinTime}\n'
    if player.leaveTime:
        info_text += f' | 退群时间: {player.leaveTime}\n'
    if player.uuid1 is not None and player.uuid2 is None:
        try:
            mc_id = await get_mc_id(player.uuid1)
        except:  # noqa
            info_text += f' | UUID: {player.uuid1}\n'
        else:
            if not isinstance(mc_id, str):
                info_text += f' | UUID: {player.uuid1}\n'
            else:
                info_text += f' | ID: {mc_id}\n'
        info_text += f' | 添加时间：{player.uuid1AddedTime}'
    elif player.uuid2 is not None and player.uuid1 is None:
        try:
            mc_id = await get_mc_id(player.uuid2)
        except:  # noqa
            info_text += f' | UUID: {player.uuid2}\n'
        else:
            if not isinstance(mc_id, str):
                info_text += f' | UUID: {player.uuid2}\n'
            else:
                info_text += f' | ID: {mc_id}\n'
        info_text += f' | 添加时间：{player.uuid2AddedTime}'
    elif player.uuid1 is not None and player.uuid2 is not None:
        try:
            mc_id1 = await get_mc_id(player.uuid1)
        except:  # noqa
            info_text += f' | UUID 1: {player.uuid1}\n'
        else:
            if not isinstance(mc_id1, str):
                info_text += f' | UUID 1: {player.uuid1}\n'
            else:
                info_text += f' | ID 1: {mc_id1}\n'
        info_text += f' | ID 1添加时间：{player.uuid1AddedTime}\n'
        try:
            mc_id2 = await get_mc_id(player.uuid2)
        except:  # noqa
            info_text += f' | UUID 2: {player.uuid2}\n'
        else:
            if not isinstance(mc_id2, str):
                info_text += f' | UUID 2: {player.uuid2}\n'
            else:
                info_text += f' | ID 2: {mc_id2}\n'
        info_text += f' | ID 2添加时间：{player.uuid2AddedTime}'

    return MessageChain.create(At(player.qq), Plain(info_text))
