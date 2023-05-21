import time
from asyncio.exceptions import TimeoutError as AsyncIOTimeoutError
from typing import TYPE_CHECKING

from aiohttp import ClientResponse
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain
from graia.ariadne.model import Member
from loguru import logger
from sqlalchemy.sql import func

from libs import db

from ..config import config
from ..model import Player, UUIDList
from ..rcon import execute_command
from ..utils import get_uuid
from .query import query_banned_player_by_qq, query_banned_uuid, query_player_by_qq, query_whitelist_by_uuid


async def add_whitelist_to_qq(qq: int, mc_id: str, admin: bool) -> tuple[MessageChain, bool]:
    try:
        real_mc_id, mc_uuid = await get_uuid(mc_id)
    except AsyncIOTimeoutError as e:
        logger.error(f'向 mojang 查询【{mc_id}】的 uuid 时发生了意料之外的错误')
        logger.exception(e)
        return MessageChain(Plain(f'向 mojang 查询【{mc_id}】的 uuid 时发生了意料之外的错误:  👇\n{e}')), False
    if isinstance(real_mc_id, ClientResponse):
        if real_mc_id.status == 204:
            return MessageChain(Plain('你选择的不是一个正版ID')), False
        else:
            return MessageChain(Plain(f'向 mojang 查询【{mc_id}】的 uuid 时获得意外内容:  👇\n{await real_mc_id.text()}')), False

    # 进入 isinstance(real_mc_id, ClientResponse) 并 return 后 mc_uuid 必不为 None
    if TYPE_CHECKING and mc_uuid is None:
        return MessageChain('bug'), False

    uuid_ = await query_whitelist_by_uuid(mc_uuid)
    if uuid_ is None:
        pass
    elif uuid_.qq == qq:
        return MessageChain(Plain('这个id本来就是你哒')), False
    else:
        return MessageChain(Plain('你想要这个吗？\n这个是 '), At(uuid_.qq), Plain(' 哒~')), False

    banned_uuid = await query_banned_uuid(mc_uuid)
    if banned_uuid is None:
        pass
    elif banned_uuid.uuid == mc_uuid:
        return MessageChain(Plain(f'该UUID已被封禁，封禁原因：{banned_uuid.banReason}')), False

    banned_player = await query_banned_player_by_qq(qq)
    if banned_player is not None:
        return MessageChain(Plain(f'你的账号已被封禁，封禁原因：{banned_player.banReason}')), False

    player = await query_player_by_qq(qq)
    if player is None:
        app = Ariadne.current()
        member: Member = await app.get_member(config.serverGroup, qq)
        await db.add(
            Player(
                qq=member.id,
                joinTime=(member.join_timestamp * 1000) if member.join_timestamp else None,
                hadWhitelist=True,
            )
        )

    wl_count: int = (await db.exec(func.count(UUIDList.id))).scalar()  # type: ignore
    if wl_count > 0 and not admin:
        return MessageChain(Plain(f'你已有{wl_count}个白名单，如要申请新白名单请联系管理员')), False
    else:
        await db.add(UUIDList(uuid=mc_uuid, wlAddTime=int(time.time() * 1000), operater=10086))

    try:
        res: str = await execute_command(f'whitelist add {real_mc_id}')
    except AsyncIOTimeoutError:
        return MessageChain(Plain('添加白名单时已写入数据库，但连接服务器超时，请联系管理解决')), False
    except ValueError as e:
        logger.exception(e)
        return MessageChain(Plain(f'添加白名单时已写入数据库但无法连接到服务器，请联系管理解决: 👇\n{e}')), False

    if res.startswith('Added'):
        return MessageChain(At(qq), Plain(' 呐呐呐，白名单给你!')), True
    else:
        return MessageChain(Plain(f'添加白名单时已写入数据库但服务器返回预料之外的内容: 👇\n{res}')), False
