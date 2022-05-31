#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graia.ariadne.app import Ariadne
from graia.ariadne.console import Console
from graia.ariadne.console.saya import ConsoleSchema
from graia.ariadne.message.parser.twilight import FullMatch, RegexResult, Twilight
from graia.ariadne.model import MemberPerm
from graia.saya import Channel
from loguru import logger
from prompt_toolkit.styles import Style

channel = Channel.current()
channel.meta['can_disable'] = False


@channel.use(ConsoleSchema([Twilight([FullMatch('stop')])]))
async def stop(app: Ariadne, console: Console):
    res: str = await console.prompt(
        l_prompt=[('class:warn', ' Are you sure to stop? '), ('', ' (y/n) ')],
        style=Style([('warn', 'bg:#cccccc fg:#d00000')]),
    )
    if res.lower() in {'y', 'yes'}:
        app.stop()
        console.stop()


@channel.use(ConsoleSchema([Twilight.from_command('send {target_type} {target_id} {content}')]))
async def group_chat(app: Ariadne, target_type: RegexResult, target_id: RegexResult, content: RegexResult):
    if target_type.result is None or target_id.result is None or content.result is None:
        return
    match target_type.result.display:
        case 'group':
            await app.send_group_message(int(target_id.result.display), content.result)
        case 'friend':
            await app.send_friend_message(int(target_id.result.display), content.result)
        case _:
            logger.warning('参数错误')


def get_perm_name(perm: MemberPerm):
    match perm:
        case MemberPerm.Member:
            return '群成员'
        case MemberPerm.Administrator:
            return '管理员'
        case MemberPerm.Owner:
            return '群主'


@channel.use(ConsoleSchema([Twilight.from_command('list {target_type}')]))
async def list_target(app: Ariadne, target_type: RegexResult):
    if target_type.result is None:
        return
    match target_type.result.display:
        case 'group':
            for group in await app.get_groupList():
                logger.opt(raw=True).info(f'{group.name}({group.id}) - {get_perm_name(group.accountPerm)}\n')
        case 'friend':
            for friend in await app.get_friendList():
                logger.opt(raw=True).info(
                    f'{friend.remark}({friend.id})'
                    + (f' - {friend.nickname}\n' if friend.nickname != friend.remark else '\n')
                )
        case _:
            logger.warning('参数错误')
