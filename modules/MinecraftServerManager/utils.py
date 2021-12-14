#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import uuid
from datetime import datetime
from typing import Optional, Tuple

import aiohttp
import regex as re
from aiohttp import ClientResponse

from .database import PlayersTable

__all__ = ['get_time', 'is_mc_id', 'is_uuid', 'get_mc_id', 'get_uuid', 'query_uuid_by_qq', 'query_qq_by_uuid']


async def get_time() -> str:
    """
    :return: 当前时间，格式1970-01-01 12:00:00
    """
    time_now = int(time.time())
    time_local = time.localtime(time_now)
    dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
    return dt


async def is_mc_id(mc_id: str) -> bool:
    """
    判断是否为合法的正版ID

    :param mc_id: 正版用户名（id）
    :return: `True`为是，`False`为否
    """
    return True if 1 <= len(mc_id) <= 16 and re.match(r'^[0-9a-zA-Z_]+$', mc_id) else False


async def is_uuid(mc_uuid: str) -> bool:
    """
    判断是否为合法uuid
    """
    try:
        uuid.UUID(mc_uuid)
    except ValueError:
        return False
    else:
        return True


async def get_uuid(mc_id: str) -> tuple[str | ClientResponse, str]:
    """
    通过 id 从 Mojang 获取 uuid

    :param mc_id: 正版用户名（id）
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.mojang.com/users/profiles/minecraft/{mc_id}') as resp:
            if resp.status == 200:
                resp_json = await resp.json()
                return resp_json['name'], resp_json['id']
            # elif resp.status == 204:
            else:
                return resp, ''


async def get_mc_id(mc_uuid: str) -> str | ClientResponse:
    """
    通过 uuid 从 Mojang 获取正版 id

    :param mc_uuid: 输入一个uuid
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://sessionserver.mojang.com/session/minecraft/profile/{mc_uuid}') as resp:
            if resp.status == 200:
                resp_json = await resp.json()
                return resp_json['name']
            # elif resp.status == 204:
            # elif resp.status == 400:
            else:
                return resp


async def query_uuid_by_qq(
    qq: int | str,
) -> Tuple[
    bool,
    Optional[datetime],
    Optional[datetime],
    Optional[str],
    Optional[datetime],
    Optional[str],
    Optional[datetime],
    Optional[bool],
    Optional[str],
]:
    try:
        data: PlayersTable = PlayersTable.get(PlayersTable.qq == qq)
    except PlayersTable.DoesNotExist:
        return False, None, None, None, None, None, None, None, None
    else:
        return (
            True,
            data.joinTimestamp,
            data.leaveTimestamp,
            str(data.uuid1) if data.uuid1 else None,
            data.uuid1AddedTime,
            str(data.uuid2) if data.uuid2 else None,
            data.uuid2AddedTime,
            data.blocked,
            data.blockReason,
        )


async def query_qq_by_uuid(mc_uuid: str) -> Optional[int]:
    target = uuid.UUID(mc_uuid)
    try:
        data: PlayersTable = PlayersTable.get((PlayersTable.uuid1 == target) | (PlayersTable.uuid2 == target))
    except PlayersTable.DoesNotExist:
        return None
    else:
        return int(data.qq)
