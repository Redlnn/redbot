#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import contextlib
from random import uniform

from graia.ariadne.app import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunched, ApplicationShutdowned
from graia.ariadne.event.message import FriendMessage
from graia.ariadne.event.mirai import (
    BotGroupPermissionChangeEvent,
    BotInvitedJoinGroupRequestEvent,
    BotJoinGroupEvent,
    BotLeaveEventActive,
    BotLeaveEventKick,
    NewFriendRequestEvent,
)
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.twilight import (
    RegexMatch,
    RegexResult,
    SpacePolicy,
    Twilight,
)
from graia.ariadne.model import Friend
from graia.ariadne.util.interrupt import FunctionWaiter
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from loguru import logger

from util import get_graia_version
from util.config import basic_cfg
from util.control import require_disable
from util.control.permission import perm_cfg

channel = Channel.current()

channel.meta['author'] = ['Red_lnn', 'A60(djkcyl)']
channel.meta['name'] = 'Bot管理'
channel.meta['description'] = '[.!！]添加群白名单 [群号]\n[.!！]添加群黑名单 [群号]\n[.!！]添加用户黑名单 [QQ号]'
channel.meta['can_disable'] = False

ASCII_LOGO = r'''
_____   _____  _____  _____  _____  _____
|  _  \ | ____||  _  \|  _  \/  _  \|_   _|
| |_| | | |__  | | | || |_| || | | |  | |
|  _  / |  __| | | | ||  _  <| | | |  | |
| | \ \ | |___ | |_| || |_| || |_| |  | |
|_|  \_\|_____||_____/|_____/\_____/  |_|'''


async def send_to_admin(message: MessageChain):
    app = Ariadne.current()
    for admin in basic_cfg.admin.admins:
        with contextlib.suppress(UnknownTarget):
            await app.send_friend_message(admin, message)
            await asyncio.sleep(uniform(0.5, 1.5))


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def launch_handler():
    logger.opt(colors=True, raw=True).info(
        f'<cyan>{ASCII_LOGO}</>',
        alt=f'[cyan]{ASCII_LOGO}[/]',
    )
    logger.success('launched!')


# @channel.use(ListenerSchema(listening_events=[ApplicationLaunched], decorators=[require_disable(channel.module)]))
# async def launched(app: Ariadne):
#     group_list = await app.get_group_list()
#     quit_groups = 0
#     # for group in groupList:
#     #     if group.id not in perm_cfg.group_whitelist:
#     #         await app.quit_group(group)
#     #         quit_groups += 1
#     msg = f'{basic_cfg.botName} 成功启动，当前共加入了 {len(group_list) - quit_groups} 个群'
#     # if quit_groups > 0:
#     #     msg += f'，本次已自动退出 {quit_groups} 个群'
#     try:
#         await app.send_friend_message(basic_cfg.admin.masterId, MessageChain(Plain(msg)))
#     except UnknownTarget:
#         logger.warning('无法向 Bot 主人发送消息，请添加 Bot 为好友')


# @channel.use(ListenerSchema(listening_events=[ApplicationShutdowned], decorators=[require_disable(channel.module)]))
# async def shutdowned(app: Ariadne):
#     try:
#         await app.send_friend_message(basic_cfg.admin.masterId, MessageChain(Plain(f'{basic_cfg.botName} 正在关闭')))
#     except UnknownTarget:
#         logger.warning('无法向 Bot 主人发送消息，请添加 Bot 为好友')


@channel.use(ListenerSchema(listening_events=[NewFriendRequestEvent]))
async def new_friend(app: Ariadne, event: NewFriendRequestEvent):
    """
    收到好友申请
    """
    if event.supplicant in basic_cfg.admin.admins:
        await event.accept()
        await app.send_friend_message(event.supplicant, MessageChain(Plain('已通过你的好友申请')))
        return

    source_group: int | None = event.source_group
    groupname = '未知'
    if source_group:
        group = await app.get_group(source_group)
        groupname = group.name if group else '未知'

    await send_to_admin(
        MessageChain(
            Plain(f'收到添加好友事件\nQQ：{event.supplicant}\n昵称：{event.nickname}\n'),
            Plain(f'来自群：{groupname}({source_group})\n') if source_group else Plain('\n来自好友搜索\n'),
            Plain(event.message) if event.message else Plain('无附加信息'),
            Plain('\n\n是否同意申请？请在10分钟内发送“同意”或“拒绝”，否则自动同意'),
        )
    )

    async def waiter(waiter_friend: Friend, waiter_message: MessageChain) -> tuple[bool, int] | None:
        if waiter_friend.id in basic_cfg.admin.admins:
            saying = waiter_message.display
            if saying == '同意':
                return True, waiter_friend.id
            elif saying == '拒绝':
                return False, waiter_friend.id
            else:
                await app.send_friend_message(waiter_friend, MessageChain(Plain('请发送同意或拒绝')))

    try:
        result, admin = await FunctionWaiter(waiter, [FriendMessage]).wait(timeout=600)
    except asyncio.exceptions.TimeoutError:
        await event.accept()
        await send_to_admin(MessageChain(Plain(f'由于超时未审核，已自动同意 {event.nickname}({event.supplicant}) 的好友请求')))
    else:
        if result:
            await event.accept()
            await send_to_admin(
                MessageChain(Plain(f'Bot 管理员 {admin} 已同意 {event.nickname}({event.supplicant}) 的好友请求')),
            )
        else:
            await event.reject('Bot 管理员拒绝了你的好友请求')
            await send_to_admin(
                MessageChain(Plain(f'Bot 管理员 {admin} 已拒绝 {event.nickname}({event.supplicant}) 的好友请求')),
            )


@channel.use(
    ListenerSchema(listening_events=[BotInvitedJoinGroupRequestEvent], decorators=[require_disable(channel.module)])
)
async def invited_join_group(app: Ariadne, event: BotInvitedJoinGroupRequestEvent):
    """
    被邀请入群
    """
    if event.source_group in perm_cfg.group_whitelist:
        await event.accept()
        await send_to_admin(
            MessageChain(
                Plain(
                    '收到邀请入群事件\n'
                    f'邀请者：{event.nickname}({event.supplicant})\n'
                    f'群号：{event.source_group}\n'
                    f'群名：{event.group_name}\n'
                    '\n该群位于白名单中，已同意加入'
                ),
            ),
        )
        return

    await send_to_admin(
        MessageChain(
            Plain(
                '收到邀请入群事件\n'
                f'邀请者：{event.nickname}({event.supplicant})\n'
                f'群号：{event.source_group}\n'
                f'群名：{event.group_name}\n'
                '\n是否同意申请？请在10分钟内发送“同意”或“拒绝”，否则自动拒绝'
            ),
        ),
    )

    async def waiter(waiter_friend: Friend, waiter_message: MessageChain) -> tuple[bool, int] | None:
        if waiter_friend.id in basic_cfg.admin.admins:
            saying = waiter_message.display
            if saying == '同意':
                return True, waiter_friend.id
            elif saying == '拒绝':
                return False, waiter_friend.id
            else:
                await app.send_friend_message(waiter_friend, MessageChain(Plain('请发送同意或拒绝')))

    try:
        result, admin = await FunctionWaiter(waiter, [FriendMessage]).wait(timeout=600)
    except asyncio.exceptions.TimeoutError:
        await event.reject('由于 Bot 管理员长时间未审核，已自动拒绝')
        await send_to_admin(
            MessageChain(
                Plain(
                    f'由于长时间未审核，已自动拒绝 {event.nickname}({event.supplicant}) '
                    f'邀请进入群 {event.group_name}({event.source_group}) 请求'
                )
            ),
        )
    else:
        if result:
            await event.accept()
            if event.source_group:
                perm_cfg.group_whitelist.append(event.source_group)
                perm_cfg.save()
            await send_to_admin(
                MessageChain(
                    Plain(
                        f'Bot 管理员 {admin} 已同意 {event.nickname}({event.supplicant}) '
                        f'邀请进入群 {event.group_name}({event.source_group}) 请求'
                    )
                ),
            )
        else:
            await event.reject('Bot 管理员拒绝加入该群')
            await send_to_admin(
                MessageChain(
                    Plain(
                        f'Bot 管理员 {admin} 已拒绝 {event.nickname}({event.supplicant}) '
                        f'邀请进入群 {event.group_name}({event.source_group}) 请求'
                    )
                ),
            )


@channel.use(ListenerSchema(listening_events=[BotJoinGroupEvent], decorators=[require_disable(channel.module)]))
async def join_group(app: Ariadne, event: BotJoinGroupEvent):
    """
    收到入群事件
    """
    member_num = len(await app.get_member_list(event.group))
    await send_to_admin(
        MessageChain(
            Plain(f'收到 Bot 入群事件\n群号：{event.group.id}\n群名：{event.group.name}\n群人数：{member_num}'),
        ),
    )

    if event.group.id not in perm_cfg.group_whitelist:
        await app.send_group_message(
            event.group,
            MessageChain(f'该群未在白名单中，将不会启用本 Bot 的绝大部分功能，如有需要请联系 {basic_cfg.admin.masterId} 申请白名单'),
        )
        # return await app.quit_group(joingroup.group.id)
    else:
        await app.send_group_message(
            event.group,
            MessageChain(
                f'我是 {basic_cfg.admin.masterName} 的机器人 {basic_cfg.botName}\n'
                f'如果有需要可以联系主人QQ『{basic_cfg.admin.masterId}』\n'
                '拉进其他群前请先添加主人为好友并说明用途，主人添加白名单后即可邀请\n'
                '直接拉进其他群也需要经过主人同意才会入群噢\n'
                '发送 .menu 可以查看功能列表，群管理员可以开启或禁用功能\n'
                '注：@我 不会触发任何功能（不过也存在部分特例）'
            ),
        )


@channel.use(ListenerSchema(listening_events=[BotLeaveEventKick], decorators=[require_disable(channel.module)]))
async def kick_group(event: BotLeaveEventKick):
    """
    被踢出群
    """
    perm_cfg.group_whitelist.remove(event.group.id)
    perm_cfg.save()

    await send_to_admin(
        MessageChain(f'收到被踢出群聊事件\n群号：{event.group.id}\n群名：{event.group.name}\n已移出白名单'),
    )


@channel.use(ListenerSchema(listening_events=[BotLeaveEventActive], decorators=[require_disable(channel.module)]))
async def leave_group(event: BotLeaveEventActive):
    """
    主动退群
    """
    perm_cfg.group_whitelist.remove(event.group.id)
    perm_cfg.save()

    await send_to_admin(
        MessageChain(f'收到主动退出群聊事件\n群号：{event.group.id}\n群名：{event.group.name}\n已移出白名单'),
    )


@channel.use(
    ListenerSchema(listening_events=[BotGroupPermissionChangeEvent], decorators=[require_disable(channel.module)])
)
async def permission_change(event: BotGroupPermissionChangeEvent):
    """
    群内权限变动
    """
    await send_to_admin(
        MessageChain(f'收到权限变动事件\n群号：{event.group.id}\n群名：{event.group.name}\n权限变更为：{event.current}'),
    )


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight(RegexMatch(r'[.!！]添加群白名单').space(SpacePolicy.FORCE), 'group' @ RegexMatch(r'\d+'))
        ],
        decorators=[require_disable(channel.module)],
    )
)
async def add_group_whitelist(app: Ariadne, friend: Friend, group: RegexResult):
    """
    添加群白名单
    """
    if friend.id not in basic_cfg.admin.admins or group.result is None:
        return
    perm_cfg.group_whitelist.append(int(group.result.display))
    perm_cfg.save()

    await app.send_friend_message(
        friend,
        MessageChain(
            Plain(f'已添加群 {group.result.display} 至白名单'),
        ),
    )


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[Twilight(RegexMatch(r'[.!！]添加用户黑名单').space(SpacePolicy.FORCE), 'qq' @ RegexMatch(r'\d+'))],
        decorators=[require_disable(channel.module)],
    )
)
async def add_qq_blacklist(app: Ariadne, friend: Friend, qq: RegexResult):
    """
    添加用户黑名单
    """
    if friend.id not in basic_cfg.admin.admins or qq.result is None:
        return
    perm_cfg.user_blacklist.append(int(qq.result.display))
    perm_cfg.save()

    await app.send_friend_message(
        friend,
        MessageChain(
            Plain(f'已添加用户 {qq.result.display} 至黑名单'),
        ),
    )
