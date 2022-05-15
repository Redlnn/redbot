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

from util.config import basic_cfg

if basic_cfg.console:
    channel = Channel.current()

    @channel.use(ConsoleSchema([Twilight([FullMatch('stop')])]))
    async def stop(app: Ariadne, console: Console):
        res: str = await console.prompt(
            l_prompt=[('class:warn', ' Are you sure to stop? '), ('', ' (y/n) ')],
            style=Style([('warn', 'bg:#cccccc fg:#d00000')]),
        )
        if res.lower() in ('y', 'yes'):
            await app.stop()
            console.stop()

    @channel.use(ConsoleSchema([Twilight.from_command('send {type} {id} {content}')]))
    async def group_chat(app: Ariadne, type: RegexResult, id: RegexResult, content: RegexResult):
        match type.result.asDisplay():  # type: ignore
            case 'group':
                await app.sendGroupMessage(int(id.result.asDisplay()), content.result)  # type: ignore
            case 'friend':
                await app.sendFriendMessage(int(id.result.asDisplay()), content.result)  # type: ignore
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

    @channel.use(ConsoleSchema([Twilight.from_command('list {type}')]))
    async def list(app: Ariadne, type: RegexResult):
        match type.result.asDisplay():  # type: ignore
            case 'group':
                for group in await app.getGroupList():
                    logger.opt(raw=True).info(f'{group.name}({group.id}) - {get_perm_name(group.accountPerm)}\n')
            case 'friend':
                for friend in await app.getFriendList():
                    logger.opt(raw=True).info(
                        f'{friend.remark}({friend.id})'
                        + (f' - {friend.nickname}\n' if friend.nickname != friend.remark else '\n')
                    )
            case _:
                logger.warning('参数错误')
