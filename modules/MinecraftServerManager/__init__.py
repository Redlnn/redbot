#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# import os
import time

from graia.ariadne.app import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.event.mirai import (MemberJoinEvent, MemberLeaveEventKick,
                                       MemberLeaveEventQuit)
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Plain, Source
from graia.ariadne.message.parser.pattern import RegexMatch
from graia.ariadne.message.parser.twilight import Sparkle, Twilight
from graia.ariadne.model import Group, Member, MemberPerm
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger

from config import config_data
from utils.Limit.Permission import Permission
# from utils.ModuleRegister import Module
from utils.TextWithImg2Img import generate_img

from .database import PlayersTable, db, init_table
from .rcon import execute_command
from .utils import is_mc_id, is_uuid, query_uuid_by_qq
from .whitelist import (add_whitelist_to_qq, del_whitelist_by_id,
                        del_whitelist_by_qq, del_whitelist_by_uuid,
                        gen_query_info_text, query_whitelist_by_id,
                        query_whitelist_by_uuid)

saya = Saya.current()
channel = Channel.current()

server_group = config_data['Modules']['MinecraftServerManager']['ServerGroup']
active_groups = (
    config_data['Modules']['MinecraftServerManager']['ActiveGroup']
    if config_data['Modules']['MinecraftServerManager']['ActiveGroup']
    else []
)

if server_group not in active_groups:
    active_groups.append(server_group)

# Module(
#         name='我的世界服务器管理',
#         config_name='MinecraftServerManager',
#         file_name=os.path.dirname(__file__),
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
    '[!！.]wl add <QQ号或@QQ> <游戏ID>  - 【管理】为某个ID绑定QQ并给予白名单\n'
    '[!！.]wl del @QQ  - 【管理】删除某个QQ的所有白名单\n'
    '[!！.]wl del qq <QQ号>  - 【管理】删除某个QQ的所有白名单\n'
    '[!！.]wl del id <游戏ID>  - 【管理】删除某个ID的白名单\n'
    '[!！.]wl del uuid <游戏ID>  - 【管理】删除某个UUID的白名单\n'
    '[!！.]wl info <@QQ或游戏ID>  - 查询被@QQ或某个ID的信息\n'
    '[!！.]wl info qq <QQ号>  - 查询某个QQ的信息\n'
    '[!！.]wl info id <游戏ID>  - 查询某个ID的信息'
)

menu_img_io = generate_img([menu])
wl_menu_img_io = generate_img([wl_menu])

is_init = False


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[ApplicationLaunched],
    )
)
async def init(app: Ariadne):
    if not config_data['Modules']['MinecraftServerManager']['Enabled']:
        saya.uninstall_channel(channel)
        return
    global is_init
    group_list = await app.getGroupList()
    groups = [group.id for group in group_list]
    for group in active_groups:
        if group not in groups:
            logger.error(f'要启用mc服务器管理的群组 {group} 不在机器人账号已加入的群组中，自动禁用')
            saya.uninstall_channel(channel)
            return
    init_table()
    try:
        PlayersTable.get(PlayersTable.group == server_group)
    except PlayersTable.DoesNotExist:
        logger.info('初始化mc服务器管理数据库中...')
        member_list = await app.getMemberList(server_group)
        data_source = []
        for member in member_list:
            try:
                PlayersTable.get((PlayersTable.group == server_group) & (PlayersTable.qq == member.id))
            except PlayersTable.DoesNotExist:
                data_source.append({'group': server_group, 'qq': member.id, 'joinTimestamp': member.joinTimestamp})
        with db.atomic():
            PlayersTable.insert_many(data_source).execute()
        logger.info('mc服务器管理数据库初始化完成')
    is_init = True


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]mc')]))],
    )
)
async def whitelist_menu(app: Ariadne, group: Group):
    if not is_init:
        return
    elif group.id not in active_groups:
        return
    await app.sendGroupMessage(group, MessageChain.create(Image(data_bytes=menu_img_io.getvalue())))


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]wl')]))],
    )
)
async def whitelist_menu(app: Ariadne, group: Group):
    if not is_init:
        return
    elif group.id not in active_groups:
        return
    await app.sendGroupMessage(group, MessageChain.create(Image(data_bytes=wl_menu_img_io.getvalue())))


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]wl\ add\ '), RegexMatch(r'.+')]))],
        decorators=[
            Permission.group_perm_check(
                MemberPerm.Administrator,
                send_alert=True,
                allow_override=False,
            )
        ],
    )
)
async def add_whitelist(app: Ariadne, group: Group, message: MessageChain):
    if not is_init:
        return
    elif group.id not in active_groups:
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


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]wl\ del\ '), RegexMatch(r'.+')]))],
        decorators=[
            Permission.group_perm_check(
                MemberPerm.Administrator,
                send_alert=True,
                allow_override=False,
            )
        ],
    )
)
async def del_whitelist(app: Ariadne, group: Group, message: MessageChain):
    if not is_init:
        return
    elif group.id not in active_groups:
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


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]wl\ info\ '), RegexMatch(r'.+')]))],
    )
)
async def info_whitelist(app: Ariadne, group: Group, message: MessageChain):
    if not is_init:
        return
    elif group.id not in active_groups:
        return
    msg = message.split(' ')

    match len(msg):
        case 3:
            if msg[2].onlyContains(At):
                target = msg[2].getFirst(At).target
                (
                    had_status, joinTimestamp, leaveTimestamp,
                    uuid1, uuid1AddedTime, uuid2, uuid2AddedTime, blocked, blockReason
                ) = await query_uuid_by_qq(target)
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
                        (
                            had_status, joinTimestamp, leaveTimestamp,
                            uuid1, uuid1AddedTime, uuid2, uuid2AddedTime, blocked, blockReason
                        ) = await query_uuid_by_qq(target)
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
                            (
                                had_status, joinTimestamp, leaveTimestamp,
                                uuid1, uuid1AddedTime, uuid2, uuid2AddedTime, blocked, blockReason
                            ) = await query_uuid_by_qq(int(target))
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


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]myid\ '), RegexMatch(r'.+')]))],
    )
)
async def myid(app: Ariadne, group: Group, member: Member, message: MessageChain):
    if not is_init:
        return
    elif group.id not in active_groups:
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


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]list')]))],
    )
)
async def get_player_list(app: Ariadne, group: Group):
    if not is_init:
        return
    elif group.id not in active_groups:
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


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]run'), RegexMatch(r'.+')]))],
        decorators=[Permission.group_perm_check(MemberPerm.Administrator, send_alert=True, allow_override=False)],
    )
)
async def run_command_list(app: Ariadne, group: Group, message: MessageChain):
    if not is_init:
        return
    elif group.id not in active_groups:
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
        await app.sendGroupMessage(group, MessageChain.create(Plain(f'服务器返回：↓\n{exec_result}')))


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(ListenerSchema(listening_events=[MemberJoinEvent]))
async def member_join(group: Group, member: Member):
    if not is_init:
        return
    elif group.id != server_group:
        return
    try:
        PlayersTable.get((PlayersTable.group == server_group) & (PlayersTable.qq == member.id))
    except PlayersTable.DoesNotExist:
        PlayersTable.create(group=server_group, qq=member.id, joinTimestamp=member.joinTimestamp)
    else:
        PlayersTable.update(
            {
                PlayersTable.joinTimestamp: member.joinTimestamp,
                PlayersTable.leaveTimestamp: None,
            }
        ).where((PlayersTable.group == server_group) & (PlayersTable.qq == member.id)).execute()


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(ListenerSchema(listening_events=[MemberLeaveEventQuit]))
async def member_leave(app: Ariadne, group: Group, member: Member):
    if not is_init:
        return
    elif group.id != server_group:
        return
    try:
        PlayersTable.get((PlayersTable.group == server_group) & (PlayersTable.qq == member.id))
    except PlayersTable.DoesNotExist:
        PlayersTable.create(
            group=server_group, qq=member.id, joinTimestamp=member.joinTimestamp, leaveTimestamp=time.time()
        )
    else:
        PlayersTable.update({PlayersTable.leaveTimestamp: time.time()}).where(
            (PlayersTable.group == server_group) & (PlayersTable.qq == member.id)
        ).execute()
        await del_whitelist_by_qq(member.id, app, group)


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(ListenerSchema(listening_events=[MemberLeaveEventKick]))
async def member_kick(app: Ariadne, group: Group, event: MemberLeaveEventKick):
    if not is_init:
        return
    elif group.id != server_group:
        return
    try:
        PlayersTable.get((PlayersTable.group == server_group) & (PlayersTable.qq == event.member.id))
    except PlayersTable.DoesNotExist:
        PlayersTable.create(
            group=server_group,
            qq=event.member.id,
            joinTimestamp=event.member.joinTimestamp,
            leaveTimestamp=time.time(),
        )
    else:
        PlayersTable.update(
            {PlayersTable.leaveTimestamp: time.time(), PlayersTable.blocked: True, PlayersTable.blockReason: 'Kick'}
        ).where((PlayersTable.group == server_group) & (PlayersTable.qq == event.member.id)).execute()
        await del_whitelist_by_qq(event.member.id, app, group)


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]pardon\ '), RegexMatch(r'.+')]))],
        decorators=[Permission.group_perm_check(MemberPerm.Administrator, send_alert=True, allow_override=False)],
    )
)
async def pardon(app: Ariadne, group: Group, message: MessageChain):
    if not is_init:
        return
    elif group.id not in active_groups:
        return
    msg = message.split(' ')
    if len(msg) != 2:
        await app.sendGroupMessage(group, MessageChain.create(Plain('无效的命令')))
        return
    elif msg[1].onlyContains(At):
        PlayersTable.update({PlayersTable.blocked: False, PlayersTable.blockReason: None}).where(
            (PlayersTable.group == server_group) & (PlayersTable.qq == msg[1].getFirst(At).target)
        ).execute()
    elif msg[1].onlyContains(Plain):
        PlayersTable.update({PlayersTable.blocked: False, PlayersTable.blockReason: None}).where(
            (PlayersTable.group == server_group) & (PlayersTable.qq == msg[1].asDisplay())
        ).execute()
    else:
        await app.sendGroupMessage(group, MessageChain.create(Plain('无效的命令')))
        return
    await app.sendGroupMessage(group, MessageChain.create(Plain('已原谅该玩家')))


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]clear_leave_time\ '), RegexMatch(r'.+')]))],
        decorators=[Permission.group_perm_check(MemberPerm.Administrator, send_alert=True, allow_override=False)],
    )
)
async def clear_leave_time(app: Ariadne, group: Group, message: MessageChain):
    if not is_init:
        return
    elif group.id not in active_groups:
        return
    msg = message.split(' ')
    if len(msg) != 2:
        await app.sendGroupMessage(group, MessageChain.create(Plain('无效的命令')))
        return
    elif msg[1].onlyContains(At):
        PlayersTable.update({PlayersTable.leaveTimestamp: None}).where(
            (PlayersTable.group == server_group) & (PlayersTable.qq == msg[1].getFirst(At).target)
        ).execute()
    elif msg[1].onlyContains(Plain):
        PlayersTable.update({PlayersTable.leaveTimestamp: None}).where(
            (PlayersTable.group == server_group) & (PlayersTable.qq == msg[1].asDisplay())
        ).execute()
    else:
        await app.sendGroupMessage(group, MessageChain.create(Plain('无效的命令')))
        return
    await app.sendGroupMessage(group, MessageChain.create(Plain('已清除该玩家的退群时间')))


# ---------------------------------------------------------------------------------------------------------------------


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]ban\ '), RegexMatch(r'.+')]))],
        decorators=[Permission.group_perm_check(MemberPerm.Administrator, send_alert=True, allow_override=False)],
    )
)
async def ban(app: Ariadne, group: Group, message: MessageChain):
    if not is_init:
        return
    elif group.id not in active_groups:
        return
    msg = message.split(' ')
    if not 2 <= len(msg) <= 3:
        await app.sendGroupMessage(group, MessageChain.create(Plain('无效的命令')))
        return
    elif msg[1].onlyContains(At):
        block_reason = msg[2].include(Plain).merge().asDisplay() if len(msg) == 3 else None
        target = msg[1].getFirst(At).target
        PlayersTable.update(
            {
                PlayersTable.blocked: True,
                PlayersTable.blockReason: block_reason,
            }
        ).where((PlayersTable.group == server_group) & (PlayersTable.qq == target)).execute()
    elif msg[1].onlyContains(Plain):
        block_reason = msg[2].include(Plain).merge().asDisplay() if len(msg) == 3 else None
        target = msg[1].asDisplay()
        PlayersTable.update(
            {
                PlayersTable.blocked: True,
                PlayersTable.blockReason: block_reason,
            }
        ).where((PlayersTable.group == server_group) & (PlayersTable.qq == target)).execute()
    else:
        await app.sendGroupMessage(group, MessageChain.create(Plain('无效的命令')))
        return
    await app.sendGroupMessage(group, MessageChain.create(Plain('已封禁该玩家')))
    await del_whitelist_by_qq(target, app, group)
