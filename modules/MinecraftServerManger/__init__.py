#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

from graia.ariadne.app import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.event.mirai import MemberJoinEvent, MemberLeaveEventKick, MemberLeaveEventQuit
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
from .database import db, get_group_players_list_table, init_group_players_list_table
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
        ' - [!！.]run <command> —— 【管理】执行服务器命令\n'
        ' - [!！.]pardon <QQ号或@QQ> —— 【管理】将一个QQ从群黑名单中移出\n'
        ' - [!！.]clear_leave_time ——【管理】 从数据库中清除一个QQ的退群时间'
)

# 生效的群组，若为空，即()，则在所有群组生效
# 格式为：active_group = (123456, 456789, 789012)
if not active_group:
    raise ValueError('active_group is not defined')

wl_menu = (
    '-----------白名单管理菜单-----------\n'
    '[!！.]wl add <QQ号或@QQ> <游戏ID>  - 【管理】为某个ID绑定QQ并给予白名单\n'
    '[!！.]wl del @QQ  - 【管理】删除某个QQ的所有白名单\n'
    '[!！.]wl del qq <QQ号>  - 【管理】删除某个QQ的所有白名单\n'
    '[!！.]wl del id <游戏ID>  - 【管理】删除某个ID的白名单\n'
    '[!！.]wl del uuid <游戏ID>  - 【管理】删除某个UUID的白名单\n'
    '[!！.]wl info <@QQ或游戏ID>  - 查询被@QQ或某个ID的信息\n'
    '[!！.]wl info qq <QQ号>  - 查询某个QQ的信息\n'
    '[!！.]wl info id <游戏ID>  - 查询某个ID的信息'
)


@channel.use(
        ListenerSchema(
                listening_events=[ApplicationLaunched],
        )
)
async def init(app: Ariadne):
    group_list = await app.getGroupList()
    groups = [group.id for group in group_list]
    if active_group not in groups:
        raise ValueError(f'要进行mc服务器管理的群组 {active_group} 不在机器人账号已加入的群组中')
    init_group_players_list_table(active_group)
    table = get_group_players_list_table(active_group)
    member_list = await app.getMemberList(active_group)
    data_source = []
    for member in member_list:
        try:
            table.get(table.qq == member.id)
        except table.DoesNotExist:
            data_source.append({'qq': member.id, 'joinTimestamp': member.joinTimestamp})
    with db.atomic():
        table.insert_many(data_source).execute()


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
    if group.id != active_group:
        return
    await app.sendGroupMessage(group, MessageChain.create(Plain(wl_menu)))


# ---------------------------------------------------------------------------------------------------------------------


class WhitelistAddMatch(Sparkle):
    prefix = RegexMatch(r'[!！.]wl\ add\ ')
    target = RegexMatch(r'.+')


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(WhitelistAddMatch)],
                decorators=[Permission.group_perm_check(MemberPerm.Administrator, send_alert=True, allow_master=False)],
        )
)
async def add_whitelist(app: Ariadne, group: Group, message: MessageChain):
    if group.id != active_group:
        return
    msg = message.split(' ')
    if len(msg) != 4:
        await app.sendGroupMessage(group, MessageChain.create(Plain('无效的命令')), quote=message.get(Source).pop(0))
        return

    if msg[2].onlyContains(Plain) and msg[2].asDisplay().isdigit():
        target = int(msg[2].asDisplay())
    elif msg[2].onlyContains(At):
        target = msg[2].getFirst(At).target
    else:
        await app.sendGroupMessage(
                group, MessageChain.create(Plain('目标用户不是有效的 QQ 号或 at 对象')), quote=message.get(Source).pop(0)
        )
        return

    mc_id = msg[3].asDisplay()
    if not msg[3].onlyContains(Plain) or not is_mc_id(mc_id):
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
                decorators=[Permission.group_perm_check(MemberPerm.Administrator, send_alert=True, allow_master=False)],
        )
)
async def del_whitelist(app: Ariadne, group: Group, message: MessageChain):
    if group.id != active_group:
        return
    msg = message.split(' ')

    match len(msg):
        case 3:
            if msg[2].onlyContains(At):
                target = msg[2].getFirst(At).target
                await del_whitelist_by_qq(target, app, group)
                return
        case 4:
            if msg[2].onlyContains(Plain):
                func = msg[2].asDisplay()
                if func == 'qq':
                    if msg[3].onlyContains(At):
                        target = msg[3].getFirst(At).target
                        await del_whitelist_by_qq(target, app, group)
                        return
                    elif msg[3].onlyContains(Plain):
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
                elif func == 'id' and msg[3].onlyContains(Plain):
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
                elif func == 'uuid' and msg[3].onlyContains(Plain):
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
    if group.id != active_group:
        return
    msg = message.split(' ')

    match len(msg):
        case 3:
            if msg[2].onlyContains(At):
                target = msg[2].getFirst(At).target
                table = get_group_players_list_table(group.id)
                (
                    had_status, joinTimestamp, leaveTimestamp,
                    uuid1, uuid1AddedTime, uuid2, uuid2AddedTime, blocked, blockReason
                ) = await query_uuid_by_qq(target, table)
                if not had_status:
                    await app.sendGroupMessage(
                            group,
                            MessageChain.create(
                                    At(target),
                                    Plain(f'({target}) 好像一个白名单都没有呢~')
                            )
                    )
                    return
                await gen_query_info_text(
                        target,
                        joinTimestamp,
                        leaveTimestamp,
                        uuid1,
                        uuid1AddedTime,
                        uuid2,
                        uuid2AddedTime,
                        blocked,
                        blockReason,
                        app,
                        group,
                )
                return
        case 4:
            if msg[2].onlyContains(Plain):
                func = msg[2].asDisplay()
                if func == 'qq':
                    if msg[3].onlyContains(At):
                        target = msg[3].getFirst(At).target
                        table = get_group_players_list_table(group.id)
                        (
                            had_status, joinTimestamp, leaveTimestamp,
                            uuid1, uuid1AddedTime, uuid2, uuid2AddedTime, blocked, blockReason
                        ) = await query_uuid_by_qq(target, table)
                        if not had_status:
                            await app.sendGroupMessage(
                                    group,
                                    MessageChain.create(
                                            At(target),
                                            Plain(f'({target}) 好像一个白名单都没有呢~')
                                    )
                            )
                            return
                        await gen_query_info_text(
                                target,
                                joinTimestamp,
                                leaveTimestamp,
                                uuid1,
                                uuid1AddedTime,
                                uuid2,
                                uuid2AddedTime,
                                blocked,
                                blockReason,
                                app,
                                group,
                        )
                        return
                    elif msg[3].onlyContains(Plain):
                        target = msg[3].asDisplay()
                        if target.isdigit():
                            table = get_group_players_list_table(group.id)
                            (
                                had_status, joinTimestamp, leaveTimestamp,
                                uuid1, uuid1AddedTime, uuid2, uuid2AddedTime, blocked, blockReason
                            ) = await query_uuid_by_qq(int(target), table)
                            if not had_status:
                                await app.sendGroupMessage(
                                        group,
                                        MessageChain.create(
                                                At(int(target)),
                                                Plain(f'({target}) 好像一个白名单都没有呢~')
                                        )
                                )
                                return
                            await gen_query_info_text(
                                    int(target),
                                    joinTimestamp,
                                    leaveTimestamp,
                                    uuid1,
                                    uuid1AddedTime,
                                    uuid2,
                                    uuid2AddedTime,
                                    blocked,
                                    blockReason,
                                    app,
                                    group,
                            )
                            return
                        else:
                            await app.sendGroupMessage(
                                    group,
                                    MessageChain.create(Plain('无效的 QQ 号')),
                                    quote=message.get(Source).pop(0)
                            )
                        return
                elif func == 'id' and msg[3].onlyContains(Plain):
                    target = msg[3].asDisplay()
                    if is_mc_id(target):
                        (
                            qq, joinTimestamp, leaveTimestamp,
                            uuid1, uuid1AddedTime, uuid2, uuid2AddedTime, blocked, blockReason
                        ) = await query_whitelist_by_id(target, app, group)
                        if qq:
                            await gen_query_info_text(
                                    qq,
                                    joinTimestamp,
                                    leaveTimestamp,
                                    uuid1,
                                    uuid1AddedTime,
                                    uuid2,
                                    uuid2AddedTime,
                                    blocked,
                                    blockReason,
                                    app,
                                    group,
                            )
                        return
                    else:
                        await app.sendGroupMessage(
                                group,
                                MessageChain.create(Plain('目标 ID 不是有效的 Minecraft 正版ID')),
                                quote=message.get(Source).pop(0)
                        )
                        return
                elif func == 'uuid' and msg[3].onlyContains(Plain):
                    target = msg[3].asDisplay()
                    if is_uuid(target):
                        (
                            qq, joinTimestamp, leaveTimestamp,
                            uuid1, uuid1AddedTime, uuid2, uuid2AddedTime, blocked, blockReason
                        ) = await query_whitelist_by_uuid(target, app, group)
                        if qq:
                            await gen_query_info_text(
                                    qq,
                                    joinTimestamp,
                                    leaveTimestamp,
                                    uuid1,
                                    uuid1AddedTime,
                                    uuid2,
                                    uuid2AddedTime,
                                    blocked,
                                    blockReason,
                                    app,
                                    group,
                            )
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
    if group.id != active_group:
        return
    msg = message.split(' ')
    if len(msg) != 2 or not msg[1].onlyContains(Plain):
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
    if group.id != active_group:
        return
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
                decorators=[Permission.group_perm_check(MemberPerm.Administrator, send_alert=True, allow_master=False)],
        )
)
async def get_player_list(app: Ariadne, group: Group, message: MessageChain):
    if group.id != active_group:
        return
    split_msg = message.split(' ')
    if len(split_msg) != 2:
        await app.sendGroupMessage(group, MessageChain.create(Plain('无效的命令')))
        return

    command = split_msg[1].asDisplay()
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


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(ListenerSchema(listening_events=[MemberJoinEvent]))
async def add_player(group: Group, member: Member):
    if group.id != active_group:
        return
    table = get_group_players_list_table(group.id)
    try:
        table.get(table.qq == member.id)
    except table.DoesNotExist:
        table.insert(qq=member.id, joinTimestamp=member.joinTimestamp).execute()
    else:
        table.update({table.joinTimestamp: member.joinTimestamp, table.leaveTimestamp: None}).where(
                table.qq == member.id
        ).execute()


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(ListenerSchema(listening_events=[MemberLeaveEventQuit]))
async def add_player(group: Group, member: Member):
    if group.id != active_group:
        return
    table = get_group_players_list_table(group.id)
    try:
        table.get(table.qq == member.id)
    except table.DoesNotExist:
        table.insert(qq=member.id, joinTimestamp=member.joinTimestamp, leaveTimestamp=time.time()).execute()
    else:
        table.update({table.leaveTimestamp: time.time()}).where(table.qq == member.id).execute()


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(ListenerSchema(listening_events=[MemberLeaveEventKick]))
async def add_player(group: Group, event: MemberLeaveEventKick):
    if group.id != active_group:
        return
    table = get_group_players_list_table(group.id)
    try:
        table.get(table.qq == event.member.id)
    except table.DoesNotExist:
        table.insert(
                qq=event.member.id,
                joinTimestamp=event.member.joinTimestamp,
                leaveTimestamp=time.time(),
                blocked=True,
                blockReason='Kick',
        ).execute()
    else:
        table.update({table.leaveTimestamp: time.time(), table.blocked: True, table.blockReason: 'Kick'}).where(
                table.qq == event.member.id
        ).execute()


# ---------------------------------------------------------------------------------------------------------------------


class PardonMatch(Sparkle):
    prefix = RegexMatch(r'[!！.]pardon\ ')
    any = RegexMatch(r'.+')


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(PardonMatch)],
                decorators=[Permission.group_perm_check(MemberPerm.Administrator, send_alert=True, allow_master=False)],
        )
)
async def pardon(app: Ariadne, group: Group, message: MessageChain):
    if group.id != active_group:
        return
    msg = message.split(' ')
    table = get_group_players_list_table(group.id)
    if len(msg) != 2:
        await app.sendGroupMessage(group, MessageChain.create(Plain('无效的命令')))
        return
    elif msg[2].onlyContains(At):
        table.update({table.blocked: False, table.blockReason: None}).where(
                table.qq == msg[2].getFirst(At).target
        ).execute()
    elif msg[2].onlyContains(Plain):
        table.update({table.blocked: False, table.blockReason: None}).where(table.qq == msg[2].asDisplay()).execute()
    await app.sendGroupMessage(group, MessageChain.create(Plain('已原谅该玩家')))


# ---------------------------------------------------------------------------------------------------------------------


class ClearLeaveTimeMatch(Sparkle):
    prefix = RegexMatch(r'[!！.]clear_leave_time\ ')
    any = RegexMatch(r'.+')


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(ClearLeaveTimeMatch)],
                decorators=[Permission.group_perm_check(MemberPerm.Administrator, send_alert=True, allow_master=False)],
        )
)
async def pardon(app: Ariadne, group: Group, message: MessageChain):
    if group.id != active_group:
        return
    msg = message.split(' ')
    table = get_group_players_list_table(group.id)
    if len(msg) != 2:
        await app.sendGroupMessage(group, MessageChain.create(Plain('无效的命令')))
        return
    elif msg[2].onlyContains(At):
        table.update({table.leaveTimestamp: None}).where(table.qq == msg[2].getFirst(At).target).execute()
    elif msg[2].onlyContains(Plain):
        table.update({table.leaveTimestamp: None}).where(table.qq == msg[2].asDisplay()).execute()
    await app.sendGroupMessage(group, MessageChain.create(Plain('已清除该玩家的退群时间')))
