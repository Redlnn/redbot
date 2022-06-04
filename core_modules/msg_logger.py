#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import time

from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain, Source
from graia.ariadne.message.parser.twilight import (
    ArgResult,
    ArgumentMatch,
    ElementMatch,
    ElementResult,
    RegexMatch,
    RegexResult,
    SpacePolicy,
    Twilight,
)
from graia.ariadne.model import Group, Member, MemberPerm
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from util.control import require_disable
from util.control.permission import GroupPermission
from util.database.log_msg import (
    get_group_talk_count,
    get_member_last_message,
    get_member_talk_count,
    log_msg,
)

channel = Channel.current()

channel.meta['name'] = '历史聊天数据记录'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = '记录聊天数据到数据库\n用法：\n'
'  [!！.]msgcount —— 【管理】获得目标最近n天内的发言次数\n'
'    参数：\n'
'      --type   member/group 目标类型，本群成员或群\n'
'      --target 【可选】群号/本群成员的QQ号/At群成员\n'
'      --day    【可选，默认7天】天数（含今天）\n'
'  [!！.]getlast <At/QQ号> —— 【管理】获取某人的最后一条发言'
channel.meta['can_disable'] = False


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], decorators=[GroupPermission.require(), require_disable(channel.module)]
    )
)
async def main(group: Group, member: Member, message: MessageChain, source: Source):
    message = message.copy()
    for ind, elem in enumerate(message[:]):
        match elem.type:
            case 'Plain' | 'At' | 'AtAll' | 'Face' | 'MarketFace' | 'Xml' | 'Json' | 'App' | 'Forward':
                continue
            case 'Poke' | 'Dice' | 'MusicShare' | 'File':
                return
            case 'Image' | 'FlashImage' | 'Voice':
                message.__root__[ind] = Plain(elem.as_persistent_string(binary=False))  # type: ignore
            case _:
                message.__root__[ind] = Plain(elem.display)
    await log_msg(
        str(group.id),
        str(member.id),
        int(time.mktime(source.time.timetuple())) - time.timezone,
        source.id,
        message.as_persistent_string(),
    )


# 获取某人指定天数内的发言条数
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    RegexMatch(r'[!！.]msgcount').space(SpacePolicy.FORCE),
                    'arg_type' @ ArgumentMatch("--type", optional=False),
                    'arg_target' @ ArgumentMatch("--target"),
                    'arg_day' @ ArgumentMatch("--day", default='7'),
                ],
            )
        ],
        decorators=[GroupPermission.require(MemberPerm.Administrator), require_disable(channel.module)],
    )
)
async def get_msg_count(group: Group, member: Member, arg_type: ArgResult, arg_target: ArgResult, arg_day: ArgResult):
    if arg_day.result is None or arg_target.result is None:
        return
    if not arg_day.result.isdigit():
        await group.send_message(MessageChain(Plain('参数错误，天数不全为数字')))
        return
    today_timestamp = int(time.mktime(datetime.date.today().timetuple()))
    target_timestamp = today_timestamp - (86400 * (int(arg_day.result) - 1))
    target: int | None = None
    if arg_type.result == 'member':
        if arg_target.matched:
            if arg_target.result.only(At):
                target = arg_target.result.get_first(At).target
            elif arg_target.result.isdigit():
                target = int(arg_target.result)
        else:
            target = member.id
    elif arg_type.result == 'group':
        if arg_target.matched:
            if arg_target.result.isdigit():
                target = int(arg_target.result)
        else:
            target = group.id
    else:
        await group.send_message(MessageChain(Plain('参数错误，目标类型不存在')))
        return

    if arg_type.result.display == 'member':
        if not target:
            await group.send_message(MessageChain(Plain('参数错误，目标不是QQ号或At对象')))
            return
        count = await get_member_talk_count(str(group.id), str(target), target_timestamp)
        if not count:
            await group.send_message(
                MessageChain(At(target), Plain(' 还木有说过话，或者是他说话了但没被记录到，又或者他根本不在这个群啊喂')),
            )
            return
        await group.send_message(MessageChain(At(target), Plain(f' 最近{arg_day.result.display}天的发言条数为 {count} 条')))
    else:
        if not target:
            await group.send_message(MessageChain(Plain('参数错误，目标不是群号')))
            return
        count = await get_group_talk_count(str(group.id), target_timestamp)
        if not count:
            await group.send_message(MessageChain(Plain(f'群 {target} 木有过发言')))
            return
        if target == group.id:
            await group.send_message(MessageChain(Plain(f'本群最近{arg_day.result.display}天的发言条数为 {count} 条')))
        else:
            await group.send_message(MessageChain(Plain(f'该群最近{arg_day.result.display}天的发言条数为 {count} 条')))


# 获取某人的最后一条发言
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    RegexMatch(r'[!！.]getlast').space(SpacePolicy.FORCE),
                    'qq' @ RegexMatch(r'\d+', optional=True),
                    'at' @ ElementMatch(At, optional=True),
                ],
            )
        ],
        decorators=[GroupPermission.require(MemberPerm.Administrator), require_disable(channel.module)],
    )
)
async def get_last_msg(group: Group, message: MessageChain, qq: RegexResult, at: ElementResult):
    if (qq.result is None and at.result is None) or qq.result is None:
        return
    if qq.matched and not at.matched:
        target = int(qq.result.display)
    elif at.matched and not qq.matched:
        target = message.get_first(At).target
    else:
        await group.send_message(MessageChain(Plain('无效的指令，参数过多')))
        return
    msg, send_time = await get_member_last_message(str(group.id), str(target))
    if not msg:
        await group.send_message(MessageChain(Plain(f'{target} 木有说过话')))
        return
    chain = MessageChain.from_persistent_string(msg)
    send = MessageChain(At(target), Plain(f' 在 {send_time} 说过最后一句话：\n')).extend(chain)
    await group.send_message(send)
