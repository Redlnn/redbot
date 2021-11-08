#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graia.ariadne.app import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain, Source
from graia.ariadne.message.parser.pattern import RegexMatch
from graia.ariadne.message.parser.twilight import Sparkle, Twilight
from graia.ariadne.model import Group, Member, MemberPerm
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger

from utils.Limit.Permission import Permission
from .config import active_group
from .database import get_group_players_list_table, init_group_players_list_table
from .rcon import execute_command
from .utils import is_mc_id, is_uuid, query_uuid_by_qq
from .whitelist import (
    add_whitelist_to_qq,
    del_whitelist_by_id,
    del_whitelist_by_qq,
    del_whitelist_by_uuid,
    gen_query_info_text,
    query_whitelist_by_id,
    query_whitelist_by_uuid,
)

channel = Channel.current()

channel.name('我的世界服务器管理')
channel.author('Red_lnn')
channel.description(
        '提供白名单管理、在线列表查询、服务器命令执行功能\n'
        '用法：\n'
        ' - [!！.]myid <mc正版id> —— 自助申请白名单\n'
        ' - [!！.]list —— 获取服务器在线列表\n'
        ' - [!！.]wl —— 白名单相关\n'
        ' - [!！.]run <command> —— 执行服务器命令（管理员）'
)

# 生效的群组，若为空，即()，则在所有群组生效
# 格式为：active_group = (123456, 456789, 789012)
if not active_group:
    raise ValueError('active_group is not defined')

wl_menu = '-----------白名单管理菜单-----------\n' \
          '!wl add [QQ号或@QQ] [游戏ID]  - 【管理】为某个ID绑定QQ并给予白名单\n' \
          '!wl del @QQ  - 【管理】删除某个QQ的所有白名单\n' \
          '!wl del qq [QQ号]  - 【管理】删除某个QQ的所有白名单\n' \
          '!wl del id [游戏ID]  - 【管理】删除某个ID的白名单\n' \
          '!wl del uuid [游戏ID]  - 【管理】删除某个UUID的白名单\n' \
          '!wl info [@QQ或游戏ID]  - 查询被@QQ或某个ID的信息\n' \
          '!wl info qq [QQ号]  - 查询某个QQ的信息\n' \
          '!wl info id [游戏ID]  - 查询某个ID的信息'


@channel.use(
        ListenerSchema(
                listening_events=[ApplicationLaunched],
        )
)
async def init_db():
    for group_id in active_group:
        init_group_players_list_table(group_id)


# ---------------------------------------------------------------------------------------------------------------------


class WhitelistMenuMatch(Sparkle):
    prefix = RegexMatch(r'[!！.]wl')


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(WhitelistMenuMatch)],
        )
)
async def whitelist_menu(app: Ariadne, group: Group):
    await app.sendGroupMessage(group, MessageChain.create(Plain(wl_menu)))


# ---------------------------------------------------------------------------------------------------------------------


class WhitelistAddMatch(Sparkle):
    prefix = RegexMatch(r'[!！.]wl\ add\ ')
    target = RegexMatch(r'.+')


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(WhitelistAddMatch)],
                decorators=[Permission.group_perm_check(MemberPerm.Administrator, send_alert=True)],
        )
)
async def add_whitelist(app: Ariadne, group: Group, message: MessageChain):
    msg = message.split(' ')
    if len(msg) != 4:
        await app.sendGroupMessage(group, MessageChain.create(Plain('无效的命令')), quote=message.get(Source).pop(0))
        return

    if msg[2].onlyHas(Plain) and msg[2].asDisplay().isdigit():
        target = int(msg[2].asDisplay())
    elif msg[2].onlyHas(At):
        target = msg[2].getFirst(At).target
    else:
        await app.sendGroupMessage(
                group, MessageChain.create(Plain('目标用户不是有效的 QQ 号或 at 对象')), quote=message.get(Source).pop(0)
        )
        return

    mc_id = msg[3].asDisplay()
    if not msg[3].onlyHas(Plain) or not is_mc_id(mc_id):
        await app.sendGroupMessage(
                group, MessageChain.create(Plain('目标 ID 不是有效的 Minecraft 正版ID')), quote=message.get(Source).pop(0)
        )
        return

    await add_whitelist_to_qq(target, mc_id, True, app, message, group)


# ---------------------------------------------------------------------------------------------------------------------


class WhitelistDelMatch(Sparkle):
    prefix = RegexMatch(r'[!！.]wl\ del\ ')
    target = RegexMatch(r'.+')


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(WhitelistDelMatch)],
                decorators=[Permission.group_perm_check(MemberPerm.Administrator, send_alert=True)],
        )
)
async def del_whitelist(app: Ariadne, group: Group, message: MessageChain):
    msg = message.split(' ')

    match len(msg):
        case 3:
            if msg[2].onlyHas(At):
                target = msg[2].getFirst(At).target
                await del_whitelist_by_qq(target, app, group)
                return
        case 4:
            if msg[2].onlyHas(Plain):
                func = msg[2].asDisplay()
                if func == 'qq':
                    if msg[3].onlyHas(At):
                        target = msg[3].getFirst(At).target
                        await del_whitelist_by_qq(target, app, group)
                        return
                    elif msg[3].onlyHas(Plain):
                        target = msg[3].asDisplay()
                        if target.isdigit():
                            await del_whitelist_by_qq(int(target), app, group)
                        else:
                            await app.sendGroupMessage(
                                    group,
                                    MessageChain.create(Plain('无效的 QQ 号')),
                                    quote=message.get(Source).pop(0)
                            )
                        return
                elif func == 'id' and msg[3].onlyHas(Plain):
                    target = msg[3].asDisplay()
                    if is_mc_id(target):
                        await del_whitelist_by_id(target, app, group)
                    else:
                        await app.sendGroupMessage(
                                group,
                                MessageChain.create(Plain('目标 ID 不是有效的 Minecraft 正版ID')),
                                quote=message.get(Source).pop(0)
                        )
                        return
                elif func == 'uuid' and msg[3].onlyHas(Plain):
                    target = msg[3].asDisplay()
                    if is_uuid(target):
                        await del_whitelist_by_uuid(target, app, group)
                    else:
                        await app.sendGroupMessage(
                                group,
                                MessageChain.create(Plain('目标不是有效的 UUID')),
                                quote=message.get(Source).pop(0)
                        )
                        return

    await app.sendGroupMessage(group, MessageChain.create(Plain('无效的命令')), quote=message.get(Source).pop(0))


# ---------------------------------------------------------------------------------------------------------------------


class WhitelistInfoMatch(Sparkle):
    prefix = RegexMatch(r'[!！.]wl\ info\ ')
    target = RegexMatch(r'.+')


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(WhitelistInfoMatch)],
        )
)
async def info_whitelist(app: Ariadne, group: Group, message: MessageChain):
    msg = message.split(' ')

    match len(msg):
        case 3:
            if msg[2].onlyHas(At):
                target = msg[2].getFirst(At).target
                table = get_group_players_list_table(group.id)
                (
                    had_status, uuid1, uuid1AddedTime, uuid2, uuid2AddedTime, blocked, blockReason
                ) = await query_uuid_by_qq(target, table)
                if not had_status:
                    await app.sendGroupMessage(group,
                                               MessageChain.create(At(target), Plain(f'({target}) 好像一个白名单都没有呢~')))
                    return
                await gen_query_info_text(
                        target,
                        uuid1,
                        uuid1AddedTime,
                        uuid2,
                        uuid2AddedTime,
                        blocked,
                        blockReason,
                        app,
                        group
                )
                return
        case 4:
            if msg[2].onlyHas(Plain):
                func = msg[2].asDisplay()
                if func == 'qq':
                    if msg[3].onlyHas(At):
                        target = msg[3].getFirst(At).target
                        table = get_group_players_list_table(group.id)
                        (
                            had_status, uuid1, uuid1AddedTime, uuid2, uuid2AddedTime, blocked, blockReason
                        ) = await query_uuid_by_qq(target, table)
                        if not had_status:
                            await app.sendGroupMessage(group, MessageChain.create(At(target),
                                                                                  Plain(f'({target}) 好像一个白名单都没有呢~')))
                            return
                        await gen_query_info_text(
                                target,
                                uuid1,
                                uuid1AddedTime,
                                uuid2,
                                uuid2AddedTime,
                                blocked,
                                blockReason,
                                app,
                                group
                        )
                        return
                    elif msg[3].onlyHas(Plain):
                        target = msg[3].asDisplay()
                        if target.isdigit():
                            table = get_group_players_list_table(group.id)
                            (
                                had_status, uuid1, uuid1AddedTime, uuid2, uuid2AddedTime, blocked, blockReason
                            ) = await query_uuid_by_qq(int(target), table)
                            if not had_status:
                                await app.sendGroupMessage(group, MessageChain.create(At(int(target)), Plain(
                                        f'({target}) 好像一个白名单都没有呢~')))
                                return
                            await gen_query_info_text(
                                    int(target),
                                    uuid1,
                                    uuid1AddedTime,
                                    uuid2,
                                    uuid2AddedTime,
                                    blocked,
                                    blockReason,
                                    app,
                                    group
                            )
                            return
                        else:
                            await app.sendGroupMessage(
                                    group,
                                    MessageChain.create(Plain('无效的 QQ 号')),
                                    quote=message.get(Source).pop(0)
                            )
                        return
                elif func == 'id' and msg[3].onlyHas(Plain):
                    target = msg[3].asDisplay()
                    if is_mc_id(target):
                        (
                            qq, uuid1, uuid1AddedTime, uuid2, uuid2AddedTime, blocked, blockReason
                        ) = await query_whitelist_by_id(target, app, group)
                        if qq:
                            await gen_query_info_text(qq, uuid1, uuid1AddedTime, uuid2, uuid2AddedTime, blocked,
                                                      blockReason, app, group)
                        return
                    else:
                        await app.sendGroupMessage(
                                group,
                                MessageChain.create(Plain('目标 ID 不是有效的 Minecraft 正版ID')),
                                quote=message.get(Source).pop(0)
                        )
                        return
                elif func == 'uuid' and msg[3].onlyHas(Plain):
                    target = msg[3].asDisplay()
                    if is_uuid(target):
                        (
                            qq, uuid1, uuid1AddedTime, uuid2, uuid2AddedTime, blocked, blockReason
                        ) = await query_whitelist_by_uuid(target, app, group)
                        if qq:
                            await gen_query_info_text(qq, uuid1, uuid1AddedTime, uuid2, uuid2AddedTime, blocked,
                                                      blockReason, app, group)
                        return
                    else:
                        await app.sendGroupMessage(
                                group,
                                MessageChain.create(Plain('目标不是有效的 UUID')),
                                quote=message.get(Source).pop(0)
                        )
                        return

    await app.sendGroupMessage(group, MessageChain.create(Plain('无效的命令')), quote=message.get(Source).pop(0))


# ---------------------------------------------------------------------------------------------------------------------


class MyIdMatch(Sparkle):
    prefix = RegexMatch(r'[!！.]myid\ ')
    target = RegexMatch(r'.+')


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(MyIdMatch)],
        )
)
async def add_whitelist(app: Ariadne, group: Group, member: Member, message: MessageChain):
    msg = message.split(' ')
    if len(msg) != 2 or not msg[1].onlyHas(Plain):
        await app.sendGroupMessage(group, MessageChain.create(Plain('无效的命令')), quote=message.get(Source).pop(0))
        return

    mc_id = msg[1].asDisplay()
    if not is_mc_id(mc_id):
        await app.sendGroupMessage(
                group, MessageChain.create(Plain('目标 ID 不是有效的 Minecraft 正版ID')), quote=message.get(Source).pop(0)
        )
        return

    target = member.id

    await add_whitelist_to_qq(target, mc_id, False, app, message, group)


# @group_command('!myid', ['！myid'], '服务器管理-自助获取白名单', group=active_group)
# async def myid(app: Ariadne, member: Member, message: MessageChain, group: Group):
#     args = message.asDisplay().strip()[1:].strip().split()
#     if len(args) != 2:
#         await app.sendGroupMessage(group, MessageChain.create([
#             Plain('未知命令，请检查输入是否正确')
#         ]))
#     if member.permission not in (MemberPerm.Owner, MemberPerm.Administrator):
#         res = await query_uuid_by_qq(member.id, app, message, group)
#         if res[1] == 1 or res[1] == 2:
#             await app.sendGroupMessage(group, MessageChain.create([
#                 Plain('你已有一个白名单，因此你正在申请第二个白名单，但你没有权限！\n若想删除前一个白名单或想申请小号的白名单请联系管理员')
#             ]))
#     await add_whitelist_to_qq(member.id, args[1], app, message, group)


# ---------------------------------------------------------------------------------------------------------------------


class ListMatch(Sparkle):
    prefix = RegexMatch(r'[!！.]list')


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(ListMatch)],
        )
)
async def get_player_list(app: Ariadne, group: Group):
    try:
        exec_result: str = execute_command('list')  # noqa
    except Exception as e:
        await app.sendGroupMessage(group, MessageChain.create(Plain(f'在服务器执行命令时出错：{e}')))
        logger.error('在服务器执行命令时出错')
        logger.exception(e)
        return

    player_list: list = exec_result.split(':')
    if player_list[1] == '':
        await app.sendGroupMessage(group, MessageChain.create(Plain('服务器目前没有在线玩家')))
    else:
        playerlist = player_list[0].replace('There are', '服务器在线玩家数: ').replace(' of a max of ', '/')
        playerlist = playerlist.replace('players online', '\n在线列表: ')
        await app.sendGroupMessage(group, MessageChain.create(Plain(playerlist + player_list[1].strip())))


# ---------------------------------------------------------------------------------------------------------------------


class RunMatch(Sparkle):
    prefix = RegexMatch(r'[!！.]run')
    command = RegexMatch(r'.+')


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(RunMatch)],
                decorators=[Permission.group_perm_check(MemberPerm.Administrator, send_alert=True)],
        )
)
async def get_player_list(app: Ariadne, group: Group, message: MessageChain):
    splited_msg = message.split(' ')
    if len(splited_msg) != 2:
        await app.sendGroupMessage(group, MessageChain.create(Plain('无效的命令')))
        return

    command = splited_msg[1].asDisplay()
    try:
        exec_result: str = execute_command(command)
        logger.info(f'在服务器上执行命令：{command}')
    except Exception as e:
        await app.sendGroupMessage(group, MessageChain.create(Plain(f'在服务器执行命令时出错：{e}')))
        logger.error('在服务器执行命令时出错')
        logger.exception(e)
        return

    if exec_result is None:
        await app.sendGroupMessage(group, MessageChain.create(Plain('服务器返回为空')))
    else:
        await app.sendGroupMessage(group, MessageChain.create(Plain(f'服务器返回：↓\n{command}')))
