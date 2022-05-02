#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import time
from os.path import dirname, split

from graia.ariadne.app import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.event.mirai import (
    MemberJoinEvent,
    MemberLeaveEventKick,
    MemberLeaveEventQuit,
)
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Plain, Source
from graia.ariadne.message.parser.twilight import (
    RegexMatch,
    SpacePolicy,
    Twilight,
    WildcardMatch,
)
from graia.ariadne.model import Group, Member, MemberInfo, MemberPerm
from graia.ariadne.util.interrupt import FunctionWaiter
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger
from sqlalchemy import select, update

from util.control import DisableModule
from util.control.permission import GroupPermission
from util.database import Database
from util.text2img import generate_img

from .config import config
from .model import PlayerInfo
from .rcon import execute_command
from .utils import get_mc_id, is_mc_id, is_uuid
from .whitelist.append import add_whitelist_to_qq
from .whitelist.delete import (
    del_whitelist_by_id,
    del_whitelist_by_qq,
    del_whitelist_by_uuid,
)
from .whitelist.query import (
    gen_query_info_text,
    query_uuid_by_qq,
    query_whitelist_by_id,
    query_whitelist_by_uuid,
)

saya = Saya.current()
channel = Channel.current()
module_name = split(dirname(__file__))[-1]

# from utils.module_register import Module
# Module(
#         name='我的世界服务器管理',
#         file_name=module_name,
#         author=['Red_lnn'],
#         description='提供白名单管理、在线列表查询、服务器命令执行功能',
#         usage=(
#             ' - [!！.]myid <mc正版id> —— 自助申请白名单\n'
#             ' - [!！.]list —— 获取服务器在线列表\n'
#             ' - [!！.]wl —— 白名单相关的菜单\n'
#             ' - [!！.]run <command> —— 【管理】执行服务器命令\n'
#             ' - [!！.]ban <QQ号或@QQ> [原因] —— 【管理】从服务器封禁一个QQ及其账号\n'
#             ' - [!！.]pardon <QQ号或@QQ> —— 【管理】将一个QQ从黑名单中移出\n'
#             ' - [!！.]clear_leave_time ——【管理】从数据库中清除一个QQ的退群时间'
#         )
# ).register()

menu = (
    '-----------服务器管理菜单-----------\n'
    ' - [!！.]myid <mc正版id> —— 自助申请白名单\n'
    ' - [!！.]list —— 获取服务器在线列表\n'
    ' - [!！.]wl —— 白名单相关的菜单\n'
    ' - [!！.]run <command> —— 【管理】执行服务器命令\n'
    ' - [!！.]ban <QQ号或@QQ> [原因] —— 【管理】从服务器封禁一个QQ及其账号\n'
    ' - [!！.]pardon <QQ号或@QQ> —— 【管理】将一个QQ从黑名单中移出\n'
    ' - [!！.]clear_leave_time ——【管理】从数据库中清除一个QQ的退群时间'
)

wl_menu = (
    '-----------白名单管理菜单-----------\n'
    '[!！.]wl add <QQ号或@QQ> <游戏ID> —— 【管理】为某个ID绑定QQ并给予白名单\n'
    '[!！.]wl del @QQ —— 【管理】删除某个QQ的所有白名单\n'
    '[!！.]wl del qq <QQ号> —— 【管理】删除某个QQ的所有白名单\n'
    '[!！.]wl del id <游戏ID> —— 【管理】删除某个ID的白名单\n'
    '[!！.]wl del uuid <游戏ID> —— 【管理】删除某个UUID的白名单\n'
    '[!！.]wl info <@QQ或游戏ID> —— 查询被@QQ或某个ID的信息\n'
    '[!！.]wl info qq <QQ号> —— 查询某个QQ的信息\n'
    '[!！.]wl info id <游戏ID> —— 查询某个ID的信息\n'
    '[!！.]wl clear —— 【管理】清空数据库中的白名单信息（服务器端请自行处理）\n'
)

menu_img_bytes = generate_img([menu])
wl_menu_img_bytes = generate_img([wl_menu])

is_init = False


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched], decorators=[DisableModule.require(module_name)]))
async def init(app: Ariadne):
    global is_init
    group_list = await app.getGroupList()
    groups = [group.id for group in group_list]
    for group in config.activeGroups:
        if group not in groups:
            logger.error(f'要启用mc服务器管理的群组 {group} 不在机器人账号已加入的群组中，自动禁用')
            saya.uninstall_channel(channel)
            return
    result = await Database.select_all(select(PlayerInfo))
    if len(result) == 0:
        logger.info('初始化mc服务器管理数据库中...')
        member_list = await app.getMemberList(config.serverGroup)
        data = []
        for member in member_list:
            data.append(PlayerInfo(qq=str(member.id), join_time=member.joinTimestamp))
        if await Database.add_many(*data):
            logger.info('mc服务器管理数据库初始化完成')
        else:
            logger.error('mc服务器管理数据库初始化失败')
    is_init = True


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]mc')])],
        decorators=[GroupPermission.require()],
    )
)
async def main_menu(app: Ariadne, group: Group):
    if not is_init:
        return
    elif group.id not in config.activeGroups:
        return
    await app.sendMessage(group, MessageChain.create(Image(data_bytes=menu_img_bytes)))


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]wl')])],
        decorators=[GroupPermission.require()],
    )
)
async def whitelist_menu(app: Ariadne, group: Group, message: MessageChain):
    if not is_init:
        return
    elif group.id not in config.activeGroups:
        return
    if len(message.asDisplay()[1:]) == 2:
        await app.sendMessage(group, MessageChain.create(Image(data_bytes=wl_menu_img_bytes)))


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]wl add').space(SpacePolicy.FORCE), WildcardMatch()])],
        decorators=[
            GroupPermission.require(MemberPerm.Administrator),
        ],
    )
)
async def add_whitelist(app: Ariadne, group: Group, source: Source, message: MessageChain):
    if not is_init:
        await app.sendMessage(group, MessageChain.create(Plain('数据库初始化中，请稍后...')))
    elif group.id not in config.activeGroups:
        return
    msg = message.split(' ')
    if len(msg) != 4:
        await app.sendMessage(group, MessageChain.create(Plain('无效的命令')), quote=source)
        return

    if msg[2].onlyContains(Plain) and msg[2].asDisplay().isdigit():
        target = int(msg[2].asDisplay())
    elif msg[2].onlyContains(At):
        target = msg[2].getFirst(At).target
    else:
        await app.sendMessage(group, MessageChain.create(Plain('目标用户不是有效的 QQ 号或 at 对象')), quote=source)
        return

    mc_id = msg[3].asDisplay()
    if not msg[3].onlyContains(Plain) or not await is_mc_id(mc_id):
        await app.sendMessage(group, MessageChain.create(Plain('目标 ID 不是有效的 Minecraft 正版ID')), quote=source)
        return

    await app.sendMessage(group, await add_whitelist_to_qq(target, mc_id, True), quote=source)


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]wl del').space(SpacePolicy.FORCE), WildcardMatch()])],
        decorators=[
            GroupPermission.require(
                MemberPerm.Administrator,
            ),
        ],
    )
)
async def del_whitelist(app: Ariadne, group: Group, source: Source, message: MessageChain):
    if not is_init:
        return
    elif group.id not in config.activeGroups:
        return
    msg = message.split(' ')

    match len(msg):
        case 3:
            if msg[2].onlyContains(At):
                target = msg[2].getFirst(At).target
                await app.sendMessage(group, await del_whitelist_by_qq(target), quote=source)
                return
        case 4:
            if msg[2].onlyContains(Plain):
                func = msg[2].asDisplay()
                if func == 'qq':
                    if msg[3].onlyContains(At):
                        target = msg[3].getFirst(At).target
                        await app.sendMessage(group, await del_whitelist_by_qq(target), quote=source)
                        return
                    elif msg[3].onlyContains(Plain):
                        target = msg[3].asDisplay()
                        if target.isdigit():
                            await app.sendMessage(group, await del_whitelist_by_qq(int(target)), quote=source)
                        else:
                            await app.sendMessage(group, MessageChain.create(Plain('无效的 QQ 号')), quote=source)
                        return
                    else:
                        await app.sendMessage(group, MessageChain.create(Plain('参数错误，无效的命令')), quote=source)
                elif func == 'id' and msg[3].onlyContains(Plain):
                    target = msg[3].asDisplay()
                    if await is_mc_id(target):
                        await app.sendMessage(group, await del_whitelist_by_id(target), quote=source)
                    else:
                        await app.sendMessage(
                            group,
                            MessageChain.create(Plain('目标 ID 不是有效的 Minecraft 正版ID')),
                            quote=source,
                        )
                    return
                elif func == 'uuid' and msg[3].onlyContains(Plain):
                    target = msg[3].asDisplay()
                    if await is_uuid(target):
                        await app.sendMessage(group, await del_whitelist_by_uuid(target), quote=source)
                    else:
                        await app.sendMessage(group, MessageChain.create(Plain('目标不是有效的 UUID')), quote=source)
                        return

    await app.sendMessage(group, MessageChain.create(Plain('参数错误，无效的命令')), quote=source)


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]wl info').space(SpacePolicy.FORCE), WildcardMatch()])],
        decorators=[GroupPermission.require()],
    )
)
async def info_whitelist(app: Ariadne, group: Group, source: Source, message: MessageChain):
    if not is_init:
        await app.sendMessage(group, MessageChain.create(Plain('数据库初始化中，请稍后...')))
    elif group.id not in config.activeGroups:
        return
    msg = message.split(' ')

    match len(msg):
        case 3:
            if msg[2].onlyContains(At):
                target = msg[2].getFirst(At).target
                player = await query_uuid_by_qq(target)
                if player is None:
                    await app.sendMessage(group, MessageChain.create(At(target), Plain(f' 好像一个白名单都没有呢~')), quote=source)
                    return
                await app.sendMessage(group, await gen_query_info_text(player), quote=source)
                return
        case 4:
            if msg[2].onlyContains(Plain):
                func = msg[2].asDisplay()
                if func == 'qq':
                    if msg[3].onlyContains(At):
                        target = msg[3].getFirst(At).target
                        player = await query_uuid_by_qq(target)
                        if player is None:
                            await app.sendMessage(
                                group, MessageChain.create(At(target), Plain(f' 好像一个白名单都没有呢~')), quote=source
                            )
                            return
                        await app.sendMessage(group, await gen_query_info_text(player), quote=source)
                    elif msg[3].onlyContains(Plain):
                        target = msg[3].asDisplay()
                        if target.isdigit():
                            player = await query_uuid_by_qq(int(target))
                            if player is None:
                                await app.sendMessage(
                                    group, MessageChain.create(At(int(target)), Plain(f' 好像一个白名单都没有呢~')), quote=source
                                )
                                return
                            await app.sendMessage(group, await gen_query_info_text(player), quote=source)
                        else:
                            await app.sendMessage(group, MessageChain.create(Plain('无效的 QQ 号')), quote=source)
                    else:
                        await app.sendMessage(group, MessageChain.create(Plain('参数错误，无效的命令')), quote=source)
                elif func == 'id' and msg[3].onlyContains(Plain):
                    target = msg[3].asDisplay()
                    if await is_mc_id(target):
                        status, player = await query_whitelist_by_id(target)
                        if status['code'] == 200:
                            if player is None:
                                await app.sendMessage(group, MessageChain.create(Plain(f'没有使用该 ID 的白名单')), quote=source)
                            else:
                                await app.sendMessage(group, await gen_query_info_text(player), quote=source)
                        elif status['code'] == 204:
                            await app.sendMessage(group, MessageChain.create(Plain(f'没有使用该 ID 的正版用户')), quote=source)
                        elif status['code'] == 400:
                            await app.sendMessage(group, MessageChain.create(Plain(f'无效的正版用户名')), quote=source)
                        elif status['code'] == 500:
                            await app.sendMessage(group, MessageChain.create(Plain(f'Mojang API超时')), quote=source)
                        else:
                            await app.sendMessage(
                                group, MessageChain.create(Plain(f'在查询使用该 ID 的正版用户时出错')), quote=source
                            )
                    else:
                        await app.sendMessage(
                            group,
                            MessageChain.create(Plain('目标 ID 不是有效的 Minecraft 正版ID')),
                            quote=source,
                        )
                elif func == 'uuid' and msg[3].onlyContains(Plain):
                    target = msg[3].asDisplay()
                    if await is_uuid(target):
                        player = await query_whitelist_by_uuid(target)
                        if player is None:
                            await app.sendMessage(
                                group,
                                MessageChain.create('没有使用该 UUID 的白名单'),
                                quote=source,
                            )
                        else:
                            await app.sendMessage(group, await gen_query_info_text(player), quote=source)
                    else:
                        await app.sendMessage(group, MessageChain.create(Plain('目标不是有效的 UUID')), quote=source)
                return

    await app.sendMessage(group, MessageChain.create(Plain('参数错误，无效的命令')), quote=source)


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]wl clear')])],
        decorators=[
            GroupPermission.require(MemberPerm.Administrator),
        ],
    )
)
async def clear_whitelist(app: Ariadne, group: Group, member: Member, source: Source, message: MessageChain):
    if not is_init:
        await app.sendMessage(group, MessageChain.create(Plain('数据库初始化中，请稍后...')))
    elif group.id not in config.activeGroups:
        return
    msg = message.split(' ')
    if len(msg) != 2:
        await app.sendMessage(group, MessageChain.create(Plain('参数错误，无效的命令')), quote=source)
        return

    await app.sendMessage(
        group,
        MessageChain.create(
            At(member.id),
            Plain(
                ' 你正在清空本 bot 的服务器白名单数据库，本次操作不可逆，且不影响服务器的白名单，请问是否确认要清空本 bot 的服务器白名单数据库？'
                '\n确认请在10s内发送 .confirm ，取消请发送 .cancel'
            ),
        ),
        quote=source,
    )

    async def waiter(waiter_group: Group, waiter_member: Member, waiter_message: MessageChain, waiter_source: Source):
        if waiter_group.id == group.id and waiter_member.id == member.id:
            saying = waiter_message.asDisplay()
            if saying == '.confirm':
                return True
            elif saying == '.cancel':
                return False
            else:
                await app.sendMessage(
                    group, MessageChain.create(At(member.id), Plain('请发送 .confirm 或 .cancel')), quote=waiter_source
                )

    try:
        answer: MessageChain = await FunctionWaiter(waiter, [GroupMessage]).wait(timeout=10)
    except asyncio.exceptions.TimeoutError:
        await app.sendMessage(group, MessageChain.create(Plain('已超时取消')), quote=source)
        return
    if not answer:
        await app.sendMessage(group, MessageChain.create(Plain('已取消操作')), quote=source)
        return

    logger.warning(f'管理 {member.name}({member.id}) 正在清空白名单数据库')
    result = await Database.select_all(select(PlayerInfo))
    if await Database.delete_many_exist(*[i[0] for i in result]):
        await app.sendMessage(group, MessageChain.create(Plain('已清空白名单数据库，服务器白名单请自行处理')), quote=source)
    else:
        await app.sendMessage(group, MessageChain.create(Plain('清空白名单数据库失败')), quote=source)


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]myid').space(SpacePolicy.FORCE), WildcardMatch()])],
        decorators=[GroupPermission.require()],
    )
)
async def myid(app: Ariadne, group: Group, member: Member, source: Source, message: MessageChain):
    if not is_init:
        await app.sendMessage(group, MessageChain.create(Plain('数据库初始化中，请稍后...')))
    elif group.id not in config.activeGroups:
        return
    msg = message.split(' ')
    if len(msg) != 2 or not msg[1].onlyContains(Plain):
        await app.sendMessage(group, MessageChain.create(Plain('参数错误，无效的命令')), quote=source)
        return

    mc_id = msg[1].asDisplay()
    if not await is_mc_id(mc_id):
        await app.sendMessage(group, MessageChain.create(Plain('目标 ID 不是有效的 Minecraft 正版ID')), quote=source)
        return
    if mc_id.lower() not in member.name.lower():
        try:
            await app.modifyMemberInfo(member, MemberInfo(name=mc_id))
        except UnknownTarget:
            await app.sendMessage(
                group, MessageChain.create(Plain(f'请保证你的群名片包含你要申请白名单的ID\n（发生内部错误，请联系管理员：{e}）')), quote=source
            )
            return
        else:
            await app.sendMessage(group, MessageChain.create(Plain('由于你的群名片不包含你要申请白名单的ID，已自动为你修改')), quote=source)
    target = member.id
    await app.sendMessage(
        group,
        await add_whitelist_to_qq(target, mc_id, True if member.permission >= MemberPerm.Administrator else False),
        quote=source,
    )


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]list')])],
        decorators=[GroupPermission.require()],
    )
)
async def get_player_list(app: Ariadne, group: Group):
    if group.id not in config.activeGroups:
        return
    try:
        exec_result: str = await execute_command('list')  # noqa
    except TimeoutError:
        await app.sendMessage(group, MessageChain.create(Plain('连接服务器超时')))
        logger.error('rcon连接服务器超时')
        return
    except ValueError as e:
        await app.sendMessage(group, MessageChain.create(Plain(f'在服务器执行命令时出错：{e}')))
        logger.error('在服务器执行命令时出错')
        logger.exception(e)
        return

    player_list: list = exec_result.split(':')
    if player_list[1] == '':
        await app.sendMessage(group, MessageChain.create(Plain('服务器目前没有在线玩家')))
    else:
        playerlist = player_list[0].replace('There are', '服务器在线玩家数: ').replace(' of a max of ', '/')
        playerlist = playerlist.replace('players online', '\n在线列表: ')
        await app.sendMessage(group, MessageChain.create(Plain(playerlist + player_list[1].strip())))


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]run'), WildcardMatch()])],
        decorators=[
            GroupPermission.require(MemberPerm.Administrator),
        ],
    )
)
async def run_command_list(app: Ariadne, group: Group, message: MessageChain, source: Source):
    if group.id not in config.activeGroups:
        return
    split_msg = message.asDisplay().split(' ', 1)
    if len(split_msg) != 2:
        await app.sendMessage(group, MessageChain.create(Plain('参数错误，无效的命令')), quote=source)
        return
    try:
        exec_result: str = await execute_command(split_msg[1])
        logger.info(f'在服务器上执行命令：{split_msg[1]}')
    except TimeoutError:
        await app.sendMessage(group, MessageChain.create(Plain('连接服务器超时')))
        logger.error('rcon连接服务器超时')
        return
    except ValueError as e:
        await app.sendMessage(group, MessageChain.create(Plain(f'在服务器执行命令时出错：{e}')), quote=source)
        logger.error(f'在服务器执行命令 {split_msg[1]} 时出错')
        logger.exception(e)
        return

    if not exec_result:
        await app.sendMessage(group, MessageChain.create(Plain('服务器返回为空')), quote=source)
    else:
        await app.sendMessage(group, MessageChain.create(Plain(f'服务器返回 👇\n{exec_result}')), quote=source)


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[MemberJoinEvent],
    )
)
async def member_join(group: Group, member: Member):
    if not is_init:
        return
    elif group.id != config.serverGroup:
        return
    result = await Database.select_first(select(PlayerInfo).where(PlayerInfo.qq == str(member.id)))
    if result is None:
        await Database.add(PlayerInfo(qq=str(member.id), join_time=member.joinTimestamp))
    else:
        result[0].join_time = member.joinTimestamp
        result[0].leave_time = None
        await Database.update_exist(result[0])


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[MemberLeaveEventQuit],
    )
)
async def member_leave(app: Ariadne, group: Group, member: Member):
    if not is_init:
        return
    elif group.id != config.serverGroup:
        return
    result = await Database.select_first(select(PlayerInfo).where(PlayerInfo.qq == str(member.id)))
    if result is None:
        await Database.add(PlayerInfo(qq=str(member.id), join_time=member.joinTimestamp, leave_time=int(time.time())))
    else:
        result[0].leave_time = int(time.time())
        await Database.update_exist(result[0])
        await app.sendMessage(group, await del_whitelist_by_qq(member.id))


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[MemberLeaveEventKick],
    )
)
async def member_kick(app: Ariadne, group: Group, target: Member):
    if not is_init:
        return
    elif group.id != config.serverGroup:
        return
    result = await Database.select_first(select(PlayerInfo).where(PlayerInfo.qq == target.id))
    if result is None:
        await Database.add(PlayerInfo(qq=str(target.id), join_time=target.joinTimestamp, leave_time=int(time.time())))
    else:
        result[0].leave_time = int(time.time())
        result[0].blocked = True
        result[0].block_reason = 'Kick'
        await Database.update_exist(result[0])
        await app.sendMessage(group, await del_whitelist_by_qq(target.id))


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]pardon').space(SpacePolicy.FORCE), WildcardMatch()])],
        decorators=[
            GroupPermission.require(MemberPerm.Administrator),
        ],
    )
)
async def pardon(app: Ariadne, group: Group, message: MessageChain, source: Source):
    if not is_init:
        await app.sendMessage(group, MessageChain.create(Plain('数据库初始化中，请稍后...')))
    elif group.id not in config.activeGroups:
        return
    msg = message.split(' ')
    if len(msg) != 2:
        await app.sendMessage(group, MessageChain.create(Plain('参数错误，无效的命令')), quote=source)
        return
    elif msg[1].onlyContains(At):
        target = msg[1].getFirst(At).target
        await Database.exec(
            update(PlayerInfo).where(PlayerInfo.qq == str(target)).values(blocked=False, block_reason=None)
        )
    elif msg[1].onlyContains(Plain):
        target = msg[1].asDisplay()
        if not target.isdigit():
            await app.sendMessage(group, MessageChain.create(Plain('请输入QQ号')), quote=source)
            return
        await Database.exec(update(PlayerInfo).where(PlayerInfo.qq == target).values(blocked=False, block_reason=None))
        target = int(target)
    else:
        await app.sendMessage(group, MessageChain.create(Plain('参数错误，无效的命令')), quote=source)
        return
    player = await query_uuid_by_qq(target)
    if player is None:
        await app.sendMessage(group, MessageChain.create(Plain('已解封该玩家')), quote=source)
        return
    flags = []
    if player.uuid1 is not None:
        try:
            mc_id = await get_mc_id(player.uuid1)
        except asyncio.exceptions.TimeoutError as e:
            await app.sendMessage(
                group, MessageChain.create(Plain(f'无法查询【{player.uuid1}】对应的正版id: 👇\n{e}')), quote=source
            )
            logger.error(f'无法查询【{player.uuid1}】对应的正版id')
            logger.exception(e)
            flags.append(False)
        else:
            if isinstance(mc_id, str):
                try:
                    res = await execute_command(f'pardon {mc_id}')
                except TimeoutError:
                    await app.sendMessage(group, MessageChain.create(Plain('连接服务器超时')))
                    logger.error('rcon连接服务器超时')
                    flags.append(False)
                except ValueError as e:
                    logger.exception(e)
                    flags.append(False)
                else:
                    if not res.startswith('Unbanned') and res != "Nothing changed. The player isn't banned":
                        await app.sendMessage(
                            group, MessageChain.create(Plain(f'在解封该玩家时服务器返回未知结果 👇\n{res}')), quote=source
                        )
                        flags.append(False)
            else:
                await app.sendMessage(
                    group, MessageChain.create(Plain(f'无法获取该玩家的 ID，因此无法在服务器解封该玩家\nUUID：{player.uuid1}')), quote=source
                )
                flags.append(False)
    if player.uuid2:
        try:
            mc_id = await get_mc_id(player.uuid2)
        except asyncio.exceptions.TimeoutError as e:
            await app.sendMessage(
                group, MessageChain.create(Plain(f'无法查询【{player.uuid2}】对应的正版id: 👇\n{e}')), quote=source
            )
            logger.error(f'无法查询【{player.uuid2}】对应的正版id')
            logger.exception(e)
            flags.append(False)
        else:
            if isinstance(mc_id, str):
                try:
                    res = await execute_command(f'pardon {mc_id}')
                except TimeoutError:
                    await app.sendMessage(group, MessageChain.create(Plain('连接服务器超时')))
                    logger.error('rcon连接服务器超时')
                    flags.append(False)
                except ValueError as e:
                    logger.exception(e)
                    flags.append(False)
                else:
                    if not res.startswith('Unbanned') and res != "Nothing changed. The player isn't banned":
                        await app.sendMessage(
                            group, MessageChain.create(Plain(f'在解封该玩家时服务器返回未知结果 👇\n{res}')), quote=source
                        )
                        flags.append(False)
            else:
                await app.sendMessage(
                    group, MessageChain.create(Plain(f'无法获取该玩家的 ID，因此无法在服务器解封该玩家\nUUID：{player.uuid2}')), quote=source
                )
                flags.append(False)
    if False not in flags:
        await app.sendMessage(group, MessageChain.create(Plain('已解封该玩家')), quote=source)
    else:
        await app.sendMessage(group, MessageChain.create(Plain('在服务器解封该玩家时出现错误')), quote=source)


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]clear_leave_time').space(SpacePolicy.FORCE), WildcardMatch()])],
        decorators=[
            GroupPermission.require(MemberPerm.Administrator),
        ],
    )
)
async def clear_leave_time(app: Ariadne, group: Group, message: MessageChain, source: Source):
    if not is_init:
        await app.sendMessage(group, MessageChain.create(Plain('数据库初始化中，请稍后...')))
    elif group.id not in config.activeGroups:
        return
    msg = message.split(' ')
    if len(msg) != 2:
        await app.sendMessage(group, MessageChain.create(Plain('参数错误，无效的命令')), quote=source)
        return
    elif msg[1].onlyContains(At):
        target = msg[1].getFirst(At).target
        await Database.exec(update(PlayerInfo).where(PlayerInfo.qq == str(target)).values(leave_time=None))
    elif msg[1].onlyContains(Plain):
        target = msg[1].asDisplay()
        if not target.isdigit():
            await app.sendMessage(group, MessageChain.create(Plain('请输入QQ号')), quote=source)
            return
        await Database.exec(update(PlayerInfo).where(PlayerInfo.qq == target).values(leave_time=None))
    else:
        await app.sendMessage(group, MessageChain.create(Plain('参数错误，无效的命令')), quote=source)
        return
    await app.sendMessage(group, MessageChain.create(Plain('已清除该玩家的退群时间')), quote=source)


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]ban').space(SpacePolicy.FORCE), WildcardMatch()])],
        decorators=[
            GroupPermission.require(MemberPerm.Administrator),
        ],
    )
)
async def ban(app: Ariadne, group: Group, message: MessageChain, source: Source):
    if not is_init:
        await app.sendMessage(group, MessageChain.create(Plain('数据库初始化中，请稍后...')))
    elif group.id not in config.activeGroups:
        return
    msg = message.split(' ')
    if not 2 <= len(msg) <= 3:
        await app.sendMessage(group, MessageChain.create(Plain('参数错误，无效的命令')), quote=source)
        return
    elif msg[1].onlyContains(At):
        block_reason = msg[2].include(Plain).merge().asDisplay() if len(msg) == 3 else None
        target = msg[1].getFirst(At).target
        await Database.exec(
            update(PlayerInfo).where(PlayerInfo.qq == str(target)).values(blocked=True, block_reason=block_reason)
        )
    elif msg[1].onlyContains(Plain):
        block_reason = msg[2].include(Plain).merge().asDisplay() if len(msg) == 3 else None
        target = msg[1].asDisplay()
        if not target.isdigit():
            await app.sendMessage(group, MessageChain.create(Plain('请输入QQ号')))
            return
        await Database.exec(
            update(PlayerInfo).where(PlayerInfo.qq == target).values(blocked=True, block_reason=block_reason)
        )
        target = int(target)
    else:
        await app.sendMessage(group, MessageChain.create(Plain('参数错误，无效的命令')), quote=source)
        return
    player = await query_uuid_by_qq(target)
    if player is None:
        await app.sendMessage(group, MessageChain.create(Plain('已封禁该玩家')), quote=source)
        return
    flags = []
    if player.uuid1:
        try:
            mc_id = await get_mc_id(player.uuid1)
        except asyncio.exceptions.TimeoutError as e:
            await app.sendMessage(
                group, MessageChain.create(Plain(f'无法查询【{player.uuid1}】对应的正版id: 👇\n{e}')), quote=source
            )
            logger.error(f'无法查询【{player.uuid1}】对应的正版id')
            logger.exception(e)
            flags.append(False)
        else:
            if isinstance(mc_id, str):
                try:
                    res = await execute_command(f'pardon {mc_id}')
                except TimeoutError:
                    await app.sendMessage(group, MessageChain.create(Plain('连接服务器超时')))
                    logger.error('rcon连接服务器超时')
                    flags.append(False)
                except ValueError as e:
                    logger.exception(e)
                    flags.append(False)
                else:
                    if not res.startswith('Unbanned') and res != "Nothing changed. The player isn't banned":
                        await app.sendMessage(
                            group, MessageChain.create(Plain(f'在封禁该玩家时服务器返回未知结果 👇\n{res}')), quote=source
                        )
                        flags.append(False)
            else:
                await app.sendMessage(
                    group, MessageChain.create(Plain(f'无法获取该玩家的 ID，因此无法在服务器封禁该玩家\nUUID：{player.uuid1}')), quote=source
                )
                flags.append(False)
    if player.uuid2:
        try:
            mc_id = await get_mc_id(player.uuid2)
        except asyncio.exceptions.TimeoutError as e:
            await app.sendMessage(
                group, MessageChain.create(Plain(f'无法查询【{player.uuid2}】对应的正版id: 👇\n{e}')), quote=source
            )
            logger.error(f'无法查询【{player.uuid2}】对应的正版id')
            logger.exception(e)
            flags.append(False)
        else:
            if isinstance(mc_id, str):
                try:
                    res = await execute_command(f'pardon {mc_id}')
                except TimeoutError:
                    await app.sendMessage(group, MessageChain.create(Plain('连接服务器超时')))
                    logger.error('rcon连接服务器超时')
                    flags.append(False)
                except ValueError as e:
                    logger.exception(e)
                    flags.append(False)
                else:
                    if not res.startswith('Unbanned') and res != "Nothing changed. The player isn't banned":
                        await app.sendMessage(
                            group, MessageChain.create(Plain(f'在封禁该玩家时服务器返回未知结果 👇\n{res}')), quote=source
                        )
                        flags.append(False)
            else:
                await app.sendMessage(
                    group, MessageChain.create(Plain(f'无法获取该玩家的 ID，因此无法在服务器封禁该玩家\nUUID：{player.uuid2}')), quote=source
                )
                flags.append(False)
    await app.sendMessage(group, await del_whitelist_by_qq(int(target)), quote=source)
    if False not in flags:
        await app.sendMessage(group, MessageChain.create(Plain('已封禁该玩家')), quote=source)
    else:
        await app.sendMessage(group, MessageChain.create(Plain('在服务器封禁该玩家出现错误')), quote=source)
