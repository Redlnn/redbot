from asyncio.exceptions import TimeoutError as AsyncIOTimeoutError
from uuid import UUID

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain
from sqlalchemy import select

from util.database import Database

from ..model import PlayerInfo
from ..utils import format_time, get_mc_id, get_uuid


async def query_whitelist_by_uuid(mc_uuid: str) -> PlayerInfo | None:
    query_target = UUID(mc_uuid)
    result = await Database.select_first(
        select(PlayerInfo).where((PlayerInfo.uuid1 == query_target.hex) | (PlayerInfo.uuid2 == query_target.hex))
    )
    return None if result is None or len(result) == 0 else result[0]


async def query_whitelist_by_id(mc_id: str) -> tuple[dict[str, int | str], PlayerInfo | None]:
    real_mc_id, mc_uuid = await get_uuid(mc_id)
    if not isinstance(real_mc_id, str) and real_mc_id.status != 200:
        return {'code': real_mc_id.status, 'msg': await real_mc_id.text()}, None

    return {'code': 200, 'msg': ''}, await query_whitelist_by_uuid(mc_uuid)


async def query_uuid_by_qq(
    qq: int,
) -> PlayerInfo | None:
    result = await Database.select_first(select(PlayerInfo).where(PlayerInfo.qq == str(qq)))
    return None if result is None or len(result) == 0 else result[0]


async def query_qq_by_uuid(mc_uuid: str) -> PlayerInfo | None:
    target = UUID(mc_uuid)
    result = await Database.select_first(
        select(PlayerInfo).where((PlayerInfo.uuid1 == target.hex) | (PlayerInfo.uuid2 == target.hex))
    )
    return None if result is None or len(result) == 0 else result[0]


async def gen_query_info_text(player: PlayerInfo) -> MessageChain:
    if player.blocked:
        return MessageChain(At(int(player.qq)), Plain(f' 已被封禁，封禁原因：{player.block_reason}'))
    if player.uuid1 is None and player.uuid2 is None:
        return MessageChain(At(int(player.qq)), Plain(' 一个白名单都没有呢'))
    info_text = f'({player.qq}) 的白名单信息如下：\n | 入群时间: {format_time(player.join_time or 0)}\n'
    if player.leave_time:
        info_text += f' | 退群时间: {player.leave_time}\n'
    if player.uuid1 is not None and player.uuid2 is None:
        try:
            mc_id = await get_mc_id(player.uuid1)
        except AsyncIOTimeoutError:
            info_text += f' | UUID: {player.uuid1}\n'
        else:
            info_text += f' | ID: {mc_id}\n' if isinstance(mc_id, str) else f' | UUID: {player.uuid1}\n'

        info_text += f' | 添加时间：{format_time(player.uuid1_add_time or 0)}\n'
    elif player.uuid2 is not None and player.uuid1 is None:
        try:
            mc_id = await get_mc_id(player.uuid2)
        except AsyncIOTimeoutError:
            info_text += f' | UUID: {player.uuid2}\n'
        else:
            info_text += f' | ID: {mc_id}\n' if isinstance(mc_id, str) else f' | UUID: {player.uuid2}\n'

        info_text += f' | 添加时间：{format_time(player.uuid2_add_time or 0)}'
    elif bool(player.uuid1 and player.uuid2):
        try:
            mc_id1 = await get_mc_id(player.uuid1)  # type: ignore
        except AsyncIOTimeoutError:
            info_text += f' | UUID 1: {player.uuid1}\n'
        else:
            info_text += f' | ID 1: {mc_id1}\n' if isinstance(mc_id1, str) else f' | UUID 1: {player.uuid1}\n'

        info_text += f' | ID 1添加时间：{format_time(player.uuid1_add_time or 0)}\n'
        try:
            mc_id2 = await get_mc_id(player.uuid2)  # type: ignore
        except AsyncIOTimeoutError:
            info_text += f' | UUID 2: {player.uuid2}\n'
        else:
            info_text += f' | ID 2: {mc_id2}\n' if isinstance(mc_id2, str) else f' | UUID 2: {player.uuid2}\n'

        info_text += f' | ID 2添加时间：{format_time(player.uuid2_add_time or 0)}'

    return MessageChain(At(int(player.qq)), Plain(info_text))
