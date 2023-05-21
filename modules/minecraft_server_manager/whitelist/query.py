from uuid import UUID

from aiohttp import ClientResponse
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from sqlalchemy import select

from libs import db
from libs.text2img import md2img

from ..model import BannedQQList, BannedUUIDList, Player, UUIDList
from ..utils import format_time, get_mc_id, get_uuid


async def query_whitelist_by_uuid(mc_uuid: UUID) -> UUIDList | None:
    result = await db.select_first(select(UUIDList).where(UUIDList.uuid == mc_uuid))
    return None if result is None else result[0]


async def query_whitelist_by_id(mc_id: str) -> tuple[dict[str, int | str], UUIDList | None]:
    real_mc_id, mc_uuid = await get_uuid(mc_id)
    if isinstance(real_mc_id, ClientResponse) and real_mc_id.status != 200:
        return {'code': real_mc_id.status, 'msg': await real_mc_id.text()}, None
    else:
        return {'code': 200, 'msg': ''}, await query_whitelist_by_uuid(mc_uuid)  # type: ignore


async def query_uuid_by_qq(qq: int) -> list[UUIDList] | None:
    result = await db.select_all(select(UUIDList).where(UUIDList.qq == qq))
    return None if result is None else [_[0] for _ in result]


async def query_player_by_qq(qq: int) -> Player | None:
    result = await db.select_first(select(Player).where(Player.qq == qq))
    return None if result is None else result[0]


async def query_player_by_uuid(mc_uuid: UUID) -> Player | None:
    result = await db.select_first(select(UUIDList).where(UUIDList.uuid == mc_uuid))
    if result is None:
        return None
    result = await db.select_first(select(Player).where(Player.qq == result[0].qq))
    return None if result is None else result[0]


async def query_banned_player_by_qq(qq: int) -> BannedQQList | None:
    result = await db.select_first(select(BannedQQList).where(BannedQQList.qq == qq))
    return None if result is None else result[0]


async def query_banned_uuid(mc_uuid: UUID) -> BannedUUIDList | None:
    result = await db.select_first(select(BannedUUIDList).where(BannedUUIDList.uuid == mc_uuid))
    return None if result is None else result[0]


async def gen_query_info_text(player: Player) -> MessageChain:
    tmp = f'- QQ: {player.qq}\n'
    if player.joinTime is not None:
        tmp += f'- 入群时间：{format_time(player.joinTime)}\n'
    if player.inviter is not None:
        tmp += f'- 邀请人：{player.inviter}\n'
    uuid_list = await query_uuid_by_qq(player.qq)
    if uuid_list is not None:
        for index, _ in enumerate(uuid_list):
            tmp += f'- 白名单{index}\n'
            try:
                id_ = get_mc_id(_.uuid)
            except Exception:
                tmp += f'  - id: {_.uuid}\n'
            else:
                tmp += f'  - id: {id_}\n'
            tmp += f'  - 添加时间：{format_time(_.wlAddTime)}\n'
            if _.operater:
                tmp += f'  - 添加者：{_.operater}\n'

    return MessageChain(Image(data_bytes=await md2img(tmp)))
