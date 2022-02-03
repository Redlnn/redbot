#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graia.ariadne.app import Ariadne
from graia.ariadne.console import Console
from graia.ariadne.console.saya import ConsoleSchema
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.parser.twilight import (
    FullMatch,
    ParamMatch,
    Sparkle,
    Twilight,
)
from graia.saya import Channel
from prompt_toolkit.styles import Style

channel = Channel.current()


@channel.use(ConsoleSchema([Twilight(Sparkle([FullMatch('stop')]))]))
async def stop(app: Ariadne, console: Console):
    res: str = await console.prompt(
        l_prompt=[('class:warn', ' Are you sure to stop? '), ('', ' (y/n) ')],
        style=Style([('warn', 'bg:#cccccc fg:#d00000')]),
    )
    if res.lower() in ('y', 'yes'):
        await app.stop()
        console.stop()


@channel.use(ConsoleSchema([Twilight.from_command('send_goup {0} {1}')]))
async def group_chat(app: Ariadne, spark: Sparkle):
    group, message = spark[ParamMatch]
    await app.sendGroupMessage(int(group.result.asDisplay()), message.result)


@channel.use(ConsoleSchema([Twilight.from_command('send_friend {0} {1}')]))
async def friend_chat(app: Ariadne, spark: Sparkle):
    friend, message = spark[ParamMatch]
    try:
        await app.sendFriendMessage(int(friend.result.asDisplay()), message.result)
    except UnknownTarget:
        pass
