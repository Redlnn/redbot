import time
from asyncio.exceptions import TimeoutError as AsyncIOTimeoutError
from uuid import UUID

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


async def add_whitelist_to_qq(qq: int, mc_id: str, admin: bool) -> tuple[MessageChain, bool]:
    try:
        real_mc_id, mc_uuid = await get_uuid(mc_id)
    except AsyncIOTimeoutError as e:
        logger.error(f'向 mojang 查询【{mc_id}】的 uuid 时发生了意料之外的错误')
        logger.exception(e)
        return MessageChain(Plain(f'向 mojang 查询【{mc_id}】的 uuid 时发生了意料之外的错误:  👇\n{e}')), False
    if not isinstance(real_mc_id, str):
        if real_mc_id.status == 204:
            return MessageChain(Plain('你选择的不是一个正版ID')), False
        else:
            return MessageChain(Plain(f'向 mojang 查询【{mc_id}】的 uuid 时获得意外内容:  👇\n{await real_mc_id.text()}')), False

    player = await query_whitelist_by_uuid(mc_uuid)
    if player is None:
        pass
    elif int(player.qq) == qq:
        return MessageChain(Plain('这个id本来就是你哒')), False
    else:
        return MessageChain(Plain('你想要这个吗？\n这个是 '), At(int(player.qq)), Plain(' 哒~')), False

    player = await query_uuid_by_qq(qq)
    if player is None:
        app = Ariadne.current()
        member: Member = await app.get_member(config.serverGroup, qq)
        player = PlayerInfo(qq=str(member.id), join_time=member.join_timestamp)
        await Database.add(player)
    elif player.blocked:
        return MessageChain(Plain(f'你的账号已被封禁，封禁原因：{player.block_reason}')), False

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
            return MessageChain(Plain('你已有一个白名单，如要申请第二个白名单请联系管理员')), False
    elif player.uuid1 is None:
        if admin:
            await Database.exec(
                update(PlayerInfo)
                .where(PlayerInfo.qq == str(qq))
                .values(uuid1=UUID(mc_uuid).hex, uuid1_add_time=int(time.time()))
            )
        else:
            return MessageChain(Plain('你已有一个白名单，如要申请第二个白名单请联系管理员')), False
    elif admin:
        return MessageChain(Plain('目标玩家已有两个白名单，如需添加白名单请删除至少一个')), False
    else:
        return MessageChain(Plain('你已经有两个白名单了噢')), False

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
