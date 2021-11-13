#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import os
import time
from typing import Optional

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import App, At, Json, Plain, Source, Xml
from graia.ariadne.message.parser.pattern import (ArgumentMatch,
                                                  ElementMatch, RegexMatch)
from graia.ariadne.message.parser.twilight import Sparkle, Twilight
from graia.ariadne.model import Group, Member, MemberPerm
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from config import config_data
from utils.Database.msg_history import (get_group_talk_count,
                                        get_member_last_message,
                                        get_member_talk_count, log_msg)
from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Permission import Permission
from utils.ModuleRegister import Module

saya = Saya.current()
channel = Channel.current()

Module(
    name='历史聊天数据记录',
    config_name='LogMsgHistory',
    file_name=os.path.basename(__file__),
    author=['Red_lnn'],
    description='记录聊天数据到数据库',
    usage=(
        '[!！.]msgcount —— 【管理】获得目标最近n天内的发言次数\n'
        '  参数：\n'
        '    --type   member/group 目标类型，本群成员或群\n'
        '    --target 【可选】群号/本群成员的QQ号/At群成员\n'
        '    --day    天数（含今天）\n'
        '[!！.]getlast <At/QQ号> —— 【管理】获取某人的最后一条发言'
    ),
).register()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        decorators=[group_blacklist()],
    )
)
async def main(group: Group, member: Member, message: MessageChain):
    if not config_data['Modules']['LogMsgHistory']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['LogMsgHistory']['DisabledGroup']:
        if group.id in config_data['Modules']['LogMsgHistory']['DisabledGroup']:
            return
    if message.has(App):
        await log_msg(
            group.id,
            member.id,
            int(time.mktime(message.getFirst(Source).time.timetuple())) - time.timezone,
            message.getFirst(Source).id,
            '[APP消息]',
        )
    elif message.has(Xml):
        await log_msg(
            group.id,
            member.id,
            int(time.mktime(message.getFirst(Source).time.timetuple())) - time.timezone,
            message.getFirst(Source).id,
            '[XML消息]',
        )
    elif message.has(Json):
        await log_msg(
            group.id,
            member.id,
            int(time.mktime(message.getFirst(Source).time.timetuple())) - time.timezone,
            message.getFirst(Source).id,
            '[JSON消息]',
        )
    else:
        await log_msg(
            group.id,
            member.id,
            int(time.mktime(message.getFirst(Source).time.timetuple())) - time.timezone,
            message.getFirst(Source).id,
            message.asPersistentString(),
        )


# 获取某人指定天数内的发言条数
class GetMsgCountMatch(Sparkle):
    prefix = RegexMatch(r'[!！.]msgcount')
    arg_type = ArgumentMatch("--type")
    arg_target = ArgumentMatch("--target", optional=True)
    arg_day = ArgumentMatch("--day")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(GetMsgCountMatch)],
        decorators=[group_blacklist(), Permission.group_perm_check(MemberPerm.Administrator)],
    )
)
async def get_msg_count(app: Ariadne, group: Group, member: Member, message: MessageChain, sparkle: Sparkle):
    if config_data['Modules']['LogMsgHistory']['DisabledGroup']:
        if group.id in config_data['Modules']['LogMsgHistory']['DisabledGroup']:
            return
    if not sparkle.arg_day.result.isdigit():
        await app.sendGroupMessage(group, MessageChain.create(Plain('参数错误，天数不全为数字')))
        return
    today_timestamp = int(time.mktime(datetime.date.today().timetuple()))
    target_timestamp = today_timestamp - (86400 * (int(sparkle.arg_day.result) - 1))
    target: Optional[int] = None
    if sparkle.arg_type.result == 'member':
        if sparkle.arg_target.matched:
            if sparkle.arg_target.result == '\x081_At\x08':
                target = message.getFirst(At).target
            else:
                if sparkle.arg_target.result.isdigit():
                    target = int(sparkle.arg_target.result)
        else:
            target = member.id
    elif sparkle.arg_type.result == 'group':
        if sparkle.arg_target.matched:
            if sparkle.arg_target.result.isdigit():
                target = int(sparkle.arg_target.result)
        else:
            target = group.id
    else:
        await app.sendGroupMessage(group, MessageChain.create(Plain('参数错误，目标类型不存在')))
        return

    if sparkle.arg_type.result == 'member':
        if not target:
            await app.sendGroupMessage(group, MessageChain.create(Plain('参数错误，目标不是QQ号或At对象')))
            return
        count = await get_member_talk_count(group.id, target, target_timestamp)
        if not count:
            try:
                await app.sendGroupMessage(
                    group,
                    MessageChain.create(
                        At(target),
                        Plain(f'({target}) 还木有说过话，或者是他说话了但没被记录到，又或者他根本不在这个群啊喂'),
                    ),
                )
            except UnknownTarget:
                await app.sendGroupMessage(
                    group,
                    MessageChain.create(
                        Plain(f'{target} 还木有说过话，或者是他说话了但没被记录到，又或者他根本不在这个群啊喂'),
                    ),
                )
            return
        try:
            await app.sendGroupMessage(
                group,
                MessageChain.create(
                    At(target),
                    Plain(f'({target}) 最近{sparkle.arg_day.result}天的发言条数为 {count} 条'),
                ),
            )
        except UnknownTarget:
            await app.sendGroupMessage(
                group,
                MessageChain.create(
                    Plain(f'{target}最近{sparkle.arg_day.result}天的发言条数为 {count} 条'),
                ),
            )
    else:
        if not target:
            await app.sendGroupMessage(group, MessageChain.create(Plain('参数错误，目标不是群号')))
            return
        count = await get_group_talk_count(group.id, target_timestamp)
        if not count:
            await app.sendGroupMessage(group, MessageChain.create(Plain(f'群 {target} 木有过发言')))
            return
        if target == group.id:
            await app.sendGroupMessage(
                group,
                MessageChain.create(
                    Plain(f'本群最近{sparkle.arg_day.result}天的发言条数为 {count} 条'),
                ),
            )
        else:
            await app.sendGroupMessage(
                group,
                MessageChain.create(
                    Plain(f'该群最近{sparkle.arg_day.result}天的发言条数为 {count} 条'),
                ),
            )


# 获取某人的最后一条发言
class GetMemberLastMsgMatch(Sparkle):
    prefix = RegexMatch(r'[!！.]getlast')
    qq = RegexMatch(r'\d+', optional=True)
    at = ElementMatch(At, optional=True)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(GetMemberLastMsgMatch)],
        decorators=[group_blacklist(), Permission.group_perm_check(MemberPerm.Administrator)],
    )
)
async def get_last_msg(app: Ariadne, group: Group, message: MessageChain, sparkle: Sparkle):
    if config_data['Modules']['LogMsgHistory']['DisabledGroup']:
        if group.id in config_data['Modules']['LogMsgHistory']['DisabledGroup']:
            return
    if sparkle.qq.matched and not sparkle.at.matched:
        target = int(sparkle.qq.result.asDisplay())
    elif sparkle.at.matched and not sparkle.qq.matched:
        target = message.getFirst(At).target
    else:
        await app.sendGroupMessage(group, MessageChain.create(Plain('无效的指令，参数过多')))
        return
    msg, send_time = await get_member_last_message(group.id, target)
    if not msg:
        await app.sendGroupMessage(group, MessageChain.create(Plain(f'{target} 木有说过话')))
        return
    # send_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
    chain = MessageChain.fromPersistentString(msg)
    at_send = MessageChain.create(At(target), Plain(f'({target}) 在 {send_time} 说过最后一句话：\n')).extend(chain)
    send = MessageChain.create(Plain(f'{target} 在 {send_time} 说过最后一句话：\n')).extend(chain)
    try:
        await app.sendGroupMessage(group, at_send)
    except UnknownTarget:
        await app.sendGroupMessage(group, send)
