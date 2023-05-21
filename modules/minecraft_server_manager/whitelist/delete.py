from asyncio.exceptions import TimeoutError as AsyncIOTimeoutError
from typing import TYPE_CHECKING, Literal
from uuid import UUID

from aiohttp import ClientResponse
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain
from loguru import logger

from libs import db

from ..rcon import execute_command
from ..utils import get_mc_id, get_uuid
from .query import query_uuid_by_qq, query_whitelist_by_uuid


async def del_whitelist_from_server(mc_uuid: str | UUID) -> Literal[True] | MessageChain:
    try:
        mc_id = await get_mc_id(mc_uuid)
    except AsyncIOTimeoutError as e:
        logger.error(f'无法查询【{mc_uuid}】对应的正版id')
        logger.exception(e)
        return MessageChain(Plain(f'无法查询【{mc_uuid}】对应的正版id: 👇\n{e}'))
    if not isinstance(mc_id, str):
        return MessageChain(Plain(f'向 mojang 查询【{mc_uuid}】的 uuid 时获得意外内容:  👇\n{await mc_id.text()}'))
    try:
        result = await execute_command(f'whitelist remove {mc_id}')
    except AsyncIOTimeoutError:
        return MessageChain(Plain('连接服务器超时'))
    except ValueError as e:
        logger.exception(e)
        return MessageChain(Plain(f'无法连接至服务器：{e}'))
    return (
        True
        if result.startswith('Removed ')
        else MessageChain(Plain(f'从服务器删除id为【{mc_id}】的白名单时，服务器返回意料之外的内容：👇\n{result}'))
    )


async def del_whitelist_by_qq(qq: int) -> MessageChain:
    uuid_ = await query_uuid_by_qq(qq)
    if uuid_ is None:
        return MessageChain(At(qq), Plain(' 好像一个白名单都没有呢~'))

    await db.delete_many_exist(uuid_)
    flags = []
    for _ in uuid_:
        flags.append(await del_whitelist_from_server(_.uuid))

    if all(map((lambda _: _ and isinstance(_, bool)), flags)):
        return MessageChain(At(qq), Plain(' 的白名单都删掉啦~'))

    tmp = MessageChain(Plain('只从服务器上删除了 '), At(qq), Plain(' 的部分白名单 👇\n'))
    for _ in flags:
        if isinstance(_, MessageChain):
            tmp += _ + '\n'
    return tmp


async def del_whitelist_by_id(mc_id: str) -> MessageChain:
    try:
        real_mc_id, mc_uuid = await get_uuid(mc_id)
    except AsyncIOTimeoutError as e:
        logger.error(f'向 mojang 查询【{mc_id}】的 uuid 时发生了意料之外的错误')
        logger.exception(e)
        return MessageChain(Plain(f'向 mojang 查询【{mc_id}】的 uuid 时发生了意料之外的错误:  👇\n{e}'))
    if isinstance(real_mc_id, ClientResponse):
        if real_mc_id.status == 204:
            return MessageChain(Plain('你选择的不是一个正版ID'))
        else:
            return MessageChain(Plain(f'向 mojang 查询【{mc_id}】的 uuid 时获得意外内容:  👇\n{await real_mc_id.text()}'))

    # 进入 isinstance(real_mc_id, ClientResponse) 并 return 后 mc_uuid 必不为 None
    if TYPE_CHECKING and mc_uuid is None:
        return MessageChain('bug')

    return await del_whitelist_by_uuid(mc_uuid)


async def del_whitelist_by_uuid(mc_uuid: UUID) -> MessageChain:
    player = await query_whitelist_by_uuid(mc_uuid)
    if player is None:
        return MessageChain(Plain('没有使用这个 uuid 的玩家'))

    await db.delete_exist(await query_whitelist_by_uuid(mc_uuid))
    del_result = await del_whitelist_from_server(mc_uuid)
    if del_result is True:
        return MessageChain(Plain('已从服务器删除 '), At(int(player.qq)), Plain(f' 的 uuid 为 {mc_uuid} 的白名单'))
    else:
        return del_result
