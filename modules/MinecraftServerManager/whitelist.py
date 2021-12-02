#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import uuid
from datetime import datetime
from typing import Optional, Tuple

from graia.ariadne.app import Ariadne
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain, Source
from graia.ariadne.model import Group, Member
from loguru import logger

from config import config_data

from .database import PlayersTable
from .rcon import execute_command
from .utils import get_mc_id, get_uuid, query_qq_by_uuid, query_uuid_by_qq

server_group = config_data['Modules']['MinecraftServerManager']['ServerGroup']

__all__ = [
    "add_whitelist_to_qq",
    'del_whitelist_by_id',
    'del_whitelist_by_uuid',
    'del_whitelist_by_qq',
    'query_whitelist_by_uuid',
    'query_whitelist_by_id',
    'gen_query_info_text',
]


async def add_whitelist_to_qq(
    qq: int, mc_id: str, admin: bool, app: Ariadne, message: MessageChain, group: Group
) -> None:
    try:
        real_mc_id, mc_uuid = await get_uuid(mc_id)
    # except (requests.exceptions.Timeout, urllib3.exceptions.TimeoutError):
    #     await app.sendGroupMessage(group, MessageChain.create(
    #         Plain(f'向 mojang 查询【{mc_id}】的 uuid 超时')
    #     ), quote=message.get(Source).pop(0))
    #     return
    except Exception as e:
        await app.sendGroupMessage(
            group,
            MessageChain.create([Plain(f'向 mojang 查询【{mc_id}】的 uuid 时发生了意料之外的错误:  ↓\n{e}')]),
            quote=message.get(Source).pop(0),
        )
        logger.error(f'向 mojang 查询【{mc_id}】的 uuid 时发生了意料之外的错误')
        logger.exception(e)
        return
    if not isinstance(real_mc_id, str):
        if real_mc_id.status_code == 204:
            await app.sendGroupMessage(
                group, MessageChain.create([Plain('你选择的不是一个正版ID')]), quote=message.get(Source).pop(0)
            )
            return
        else:
            await app.sendGroupMessage(
                group,
                MessageChain.create([Plain(f'向 mojang 查询【{mc_id}】的 uuid 时获得意外内容:  ↓\n{real_mc_id.text}')]),
                quote=message.get(Source).pop(0),
            )

    user = await query_qq_by_uuid(mc_uuid)
    if user == qq:
        await app.sendGroupMessage(group, MessageChain.create([Plain('这个id本来就是你哒')]), quote=message.get(Source).pop(0))
    elif isinstance(user, int):
        try:
            await app.sendGroupMessage(
                group,
                MessageChain.create(
                    [
                        Plain('你想要这个吗？\n这个是 '),
                        At(user),
                        Plain(f'({user}) 哒~'),
                    ]
                ),
                quote=message.get(Source).pop(0),
            )
        except UnknownTarget:
            await app.sendGroupMessage(
                group,
                MessageChain.create(
                    [
                        Plain(f'你想要这个吗？\n这个是 {user} 哒~\n该 QQ 疑似已退群，请联系管理员处理'),
                    ]
                ),
                quote=message.get(Source).pop(0),
            )
        return

    (
        had_status,
        joinTimestamp,
        leaveTimestamp,
        uuid1,
        uuid1AddedTime,
        uuid2,
        uuid2AddedTime,
        blocked,
        blockReason,
    ) = await query_uuid_by_qq(qq)
    if not had_status:
        member: Member = await app.getMember(group, message.getFirst(At).target)
        PlayersTable.create(
            group=server_group,
            qq=qq,
            uuid1=uuid.UUID(mc_uuid),
            uuid1AddedTime=int(time.time()),
            joinTimestamp=member.joinTimestamp,
        )
    elif blocked:
        await app.sendGroupMessage(group, MessageChain.create(Plain(f'你的账号已被封禁，封禁原因：{blockReason}')))
        return
    elif not uuid1 and not uuid2:
        PlayersTable.update(
            {PlayersTable.uuid1: uuid.UUID(mc_uuid), PlayersTable.uuid1AddedTime: int(time.time())}
        ).where((PlayersTable.group == server_group) & (PlayersTable.qq == qq)).execute()
    elif uuid1 and not uuid2:
        if admin:
            PlayersTable.update(
                {PlayersTable.uuid2: uuid.UUID(mc_uuid), PlayersTable.uuid2AddedTime: int(time.time())}
            ).where((PlayersTable.group == server_group) & (PlayersTable.qq == qq)).execute()
        else:
            await app.sendGroupMessage(
                group,
                MessageChain.create(
                    [
                        Plain('你已有一个白名单，如要申请第二个白名单请联系管理员'),
                    ]
                ),
                quote=message.get(Source).pop(0),
            )
            return
    elif uuid2 and not uuid1:
        if admin:
            PlayersTable.update(
                {PlayersTable.uuid1: uuid.UUID(mc_uuid), PlayersTable.uuid1AddedTime: int(time.time())}
            ).where((PlayersTable.group == server_group) & (PlayersTable.qq == qq)).execute()
        else:
            await app.sendGroupMessage(
                group,
                MessageChain.create(
                    [
                        Plain('你已有一个白名单，如要申请第二个白名单请联系管理员'),
                    ]
                ),
                quote=message.get(Source).pop(0),
            )
            return
    else:
        if admin:
            await app.sendGroupMessage(
                group,
                MessageChain.create(
                    [
                        Plain('目标玩家已有两个白名单，如需添加白名单请删除至少一个'),
                    ]
                ),
                quote=message.get(Source).pop(0),
            )
            return
        else:
            await app.sendGroupMessage(
                group,
                MessageChain.create(
                    [
                        Plain('你已经有两个白名单了噢'),
                    ]
                ),
                quote=message.get(Source).pop(0),
            )
            return

    try:
        res: str = execute_command(f'whitelist add {real_mc_id}')
    except Exception as e:
        await app.sendGroupMessage(
            group,
            MessageChain.create([Plain(f'添加白名单时已写入数据库但无法连接到服务器，请联系管理解决: ↓\n{str(e)}')]),
            quote=message.get(Source).pop(0),
        )
        return
    if res.startswith('Added'):
        await app.sendGroupMessage(
            group, MessageChain.create([At(qq), Plain(' 呐呐呐，白名单给你!')]), quote=message.get(Source).pop(0)
        )
    else:
        await app.sendGroupMessage(
            group,
            MessageChain.create([Plain(f'添加白名单时已写入数据库但服务器返回预料之外的内容: ↓\n{res}')]),
            quote=message.get(Source).pop(0),
        )


async def del_whitelist_from_server(mc_uuid: str, app: Ariadne, group: Group) -> bool:
    try:
        mc_id = await get_mc_id(mc_uuid)
    except Exception as e:
        await app.sendGroupMessage(group, MessageChain.create([Plain(f'无法查询【{mc_uuid}】对应的正版id: ↓\n{str(e)}')]))
        logger.error(f'无法查询【{mc_uuid}】对应的正版id')
        logger.exception(e)
        return False
    if not isinstance(mc_id, str):
        await app.sendGroupMessage(
            group,
            MessageChain.create([Plain(f'向 mojang 查询【{mc_uuid}】的 uuid 时获得意外内容:  ↓\n{mc_id.text}')]),
        )
        return False
    else:
        try:
            result = execute_command(f'whitelist remove {mc_id}')
        except Exception as e:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f'无法连接至服务器：{e}')]))
            return False
        if result.startswith('Removed '):
            return True
        else:
            await app.sendGroupMessage(
                group, MessageChain.create([Plain(f'从服务器删除id为【{mc_id}】的白名单时，服务器返回意料之外的内容：↓\n{result}')])
            )
            return False


async def del_whitelist_by_qq(qq: int, app: Ariadne, group: Group) -> None:
    (
        had_status,
        joinTimestamp,
        leaveTimestamp,
        uuid1,
        uuid1AddedTime,
        uuid2,
        uuid2AddedTime,
        blocked,
        blockReason,
    ) = await query_uuid_by_qq(qq)
    if not uuid1 and not uuid2:
        try:
            await app.sendGroupMessage(group, MessageChain.create([At(qq), Plain(f'({qq}) 好像一个白名单都没有呢~')]))
        except UnknownTarget:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f'{qq} 一个白名单都没有')]))
        return

    PlayersTable.update(
        {
            PlayersTable.uuid1: None,
            PlayersTable.uuid1AddedTime: None,
            PlayersTable.uuid2: None,
            PlayersTable.uuid2AddedTime: None,
        }
    ).where((PlayersTable.group == server_group) & (PlayersTable.qq == qq)).execute()
    target = set()
    if uuid1:
        target.add(await del_whitelist_from_server(str(uuid1), app, group))
    if uuid2:
        target.add(await del_whitelist_from_server(str(uuid2), app, group))
    if False in target and True in target:
        try:
            await app.sendGroupMessage(
                group, MessageChain.create([Plain('只从服务器上删除了 '), At(qq), Plain(f'({qq}) 的部分白名单')])
            )
        except UnknownTarget:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f'只从服务器上删除了 {qq} 的部分白名单')]))
    elif False in target:
        try:
            await app.sendGroupMessage(
                group, MessageChain.create([Plain('从服务器上删除 '), At(qq), Plain(f'({qq}) 的白名单时失败')])
            )
        except UnknownTarget:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f'从服务器上删除 {qq} 的白名单时失败')]))
    else:
        try:
            await app.sendGroupMessage(group, MessageChain.create([At(qq), Plain(f'({qq}) 的白名单都删掉啦~')]))
        except UnknownTarget:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f'{qq} 的白名单都删掉啦~')]))


async def del_whitelist_by_id(mc_id: str, app: Ariadne, group: Group):
    try:
        real_mc_id, mc_uuid = await get_uuid(mc_id)
        # except (requests.exceptions.Timeout, urllib3.exceptions.TimeoutError):
        #     await app.sendGroupMessage(group, MessageChain.create(
        #         Plain(f'向 mojang 查询【{mc_id}】的 uuid 超时')
        #     ), quote=message.get(Source).pop(0))
        #     return
    except Exception as e:
        await app.sendGroupMessage(
            group,
            MessageChain.create([Plain(f'向 mojang 查询【{mc_id}】的 uuid 时发生了意料之外的错误:  ↓\n{e}')]),
        )
        logger.error(f'向 mojang 查询【{mc_id}】的 uuid 时发生了意料之外的错误')
        logger.exception(e)
        return None, None, None
    if not isinstance(real_mc_id, str):
        if real_mc_id.status_code == 204:
            await app.sendGroupMessage(group, MessageChain.create([Plain('你选择的不是一个正版ID')]))
            return None, None, None
        else:
            await app.sendGroupMessage(
                group,
                MessageChain.create([Plain(f'向 mojang 查询【{mc_id}】的 uuid 时获得意外内容:  ↓\n{real_mc_id.text}')]),
            )
    await del_whitelist_by_uuid(mc_uuid, app, group)


async def del_whitelist_by_uuid(mc_uuid: str, app: Ariadne, group: Group) -> None:
    (
        qq,
        joinTimestamp,
        leaveTimestamp,
        uuid1,
        uuid1AddedTime,
        uuid2,
        uuid2AddedTime,
        blocked,
        blockReason,
    ) = await query_whitelist_by_uuid(mc_uuid, app, group)
    if not qq:
        return
    if uuid1.replace('-', '') == mc_uuid.replace('-', ''):
        PlayersTable.update({PlayersTable.uuid1: None, PlayersTable.uuid1AddedTime: None}).where(
            (PlayersTable.group == server_group) & (PlayersTable.qq == qq)
        ).execute()
        del_result = await del_whitelist_from_server(mc_uuid, app, group)
        if del_result:
            await app.sendGroupMessage(
                group, MessageChain.create([Plain('已从服务器删除 '), At(qq), Plain(f'({qq}) 的 uuid 为 {mc_uuid} 的白名单')])
            )
    if uuid2.replace('-', '') == mc_uuid.replace('-', ''):
        PlayersTable.update({PlayersTable.uuid2: None, PlayersTable.uuid2AddedTime: None}).where(
            (PlayersTable.group == server_group) & (PlayersTable.qq == qq)
        ).execute()
        del_result = await del_whitelist_from_server(mc_uuid, app, group)
        if del_result:
            await app.sendGroupMessage(
                group, MessageChain.create([Plain('已从服务器删除 '), At(qq), Plain(f'({qq}) 的 uuid 为 {mc_uuid} 的白名单')])
            )


async def query_whitelist_by_uuid(
    mc_uuid: str, app: Ariadne, group: Group
) -> Tuple[
    Optional[int],
    Optional[datetime],
    Optional[datetime],
    Optional[str],
    Optional[datetime],
    Optional[str],
    Optional[datetime],
    Optional[bool],
    Optional[str],
]:
    query_target = uuid.UUID(mc_uuid)
    try:
        data: PlayersTable = PlayersTable.get(
            (PlayersTable.group == server_group)
            & ((PlayersTable.uuid1 == query_target) | (PlayersTable.uuid2 == query_target))
        )
    except PlayersTable.DoesNotExist:
        await app.sendGroupMessage(group, MessageChain.create([Plain(f'好像没有使用{mc_uuid}的玩家呢~')]))
        return None, None, None, None, None, None, None, None, None
    return (
        int(data.qq),
        data.joinTimestamp,
        data.leaveTimestamp,
        str(data.uuid1) if data.uuid1 else data.uuid1,
        data.uuid1AddedTime,
        str(data.uuid2) if data.uuid2 else data.uuid2,
        data.uuid2AddedTime,
        data.blocked,
        data.blockReason,
    )


async def query_whitelist_by_id(
    mc_id: str, app: Ariadne, group: Group
) -> Tuple[
    Optional[int],
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
        real_mc_id, mc_uuid = await get_uuid(mc_id)
        # except (requests.exceptions.Timeout, urllib3.exceptions.TimeoutError):
        #     await app.sendGroupMessage(group, MessageChain.create(
        #         Plain(f'向 mojang 查询【{mc_id}】的 uuid 超时')
        #     ), quote=message.get(Source).pop(0))
        #     return
    except Exception as e:
        await app.sendGroupMessage(
            group,
            MessageChain.create([Plain(f'向 mojang 查询【{mc_id}】的 uuid 时发生了意料之外的错误:  ↓\n{e}')]),
        )
        logger.error(f'向 mojang 查询【{mc_id}】的 uuid 时发生了意料之外的错误')
        logger.exception(e)
        return None, None, None, None, None, None, None, None, None
    if not isinstance(real_mc_id, str):
        if real_mc_id.status_code == 204:
            await app.sendGroupMessage(group, MessageChain.create([Plain('你选择的不是一个正版ID')]))
            return None, None, None, None, None, None, None, None, None
        else:
            await app.sendGroupMessage(
                group,
                MessageChain.create([Plain(f'向 mojang 查询【{mc_id}】的 uuid 时获得意外内容:  ↓\n{real_mc_id.text}')]),
            )

    return await query_whitelist_by_uuid(mc_uuid, app, group)


async def gen_query_info_text(
    qq: int,
    join_timestamp: datetime,
    leave_timestamp: Optional[datetime],
    uuid1: Optional[str],
    uuid1_added_time: Optional[datetime],
    uuid2: Optional[str],
    uuid2_added_time: Optional[datetime],
    blocked: bool,
    block_reason: str,
    app: Ariadne,
    group: Group,
):
    if blocked:
        try:
            await app.sendGroupMessage(group, MessageChain.create(At(qq), Plain(f'({qq}) 已被封禁，封禁原因：{block_reason}')))
        except UnknownTarget:
            await app.sendGroupMessage(group, MessageChain.create(Plain(f'{qq} 已被封禁，封禁原因：{block_reason}')))
        return
    if not uuid1 and not uuid2:
        try:
            await app.sendGroupMessage(group, MessageChain.create(At(qq), Plain(f'({qq}) 一个白名单都没有呢')))
        except UnknownTarget:
            await app.sendGroupMessage(group, MessageChain.create(Plain(f'{qq} 一个白名单都没有呢')))
        return
    info_text = f'{qq} 的白名单信息如下：\n | 入群时间: {join_timestamp}\n'
    if leave_timestamp:
        info_text += f' | 退群时间: {leave_timestamp}\n'
    if uuid1 and not uuid2:
        try:
            mc_id = await get_mc_id(uuid1)
        except:  # noqa
            info_text += f' | UUID: {uuid1}\n'
        else:
            if not isinstance(mc_id, str):
                info_text += f' | UUID: {uuid1}\n'
            else:
                info_text += f' | ID: {mc_id}\n'
        info_text += f' | 添加时间：{uuid1_added_time}\n'
    elif uuid2 and not uuid1:
        try:
            mc_id = await get_mc_id(uuid2)
        except:  # noqa
            info_text += f' | UUID: {uuid2}\n'
        else:
            if not isinstance(mc_id, str):
                info_text += f' | UUID: {uuid2}\n'
            else:
                info_text += f' | ID: {mc_id}\n'
        info_text += f' | 添加时间：{uuid2_added_time}\n'
    elif uuid1 and uuid2:
        try:
            mc_id1 = await get_mc_id(uuid1)
        except:  # noqa
            info_text += f' | UUID 1: {uuid1}\n'
        else:
            if not isinstance(mc_id1, str):
                info_text += f' | UUID 1: {uuid1}\n'
            else:
                info_text += f' | ID 1: {mc_id1}\n'
        info_text += f' | ID 1添加时间：{uuid1_added_time}\n'
        try:
            mc_id2 = await get_mc_id(uuid2)
        except:  # noqa
            info_text += f' | UUID 2: {uuid2}\n'
        else:
            if not isinstance(mc_id2, str):
                info_text += f' | UUID 2: {uuid2}\n'
            else:
                info_text += f' | ID 2: {mc_id2}\n'
        info_text += f' | ID 2添加时间：{uuid2_added_time}\n'

    await app.sendGroupMessage(group, MessageChain.create(Plain(info_text.rstrip())))
