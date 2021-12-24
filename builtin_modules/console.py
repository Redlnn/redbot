#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graia.ariadne.app import Ariadne
from graia.ariadne.console import Console
from graia.ariadne.console.saya import ConsoleSchema
from graia.ariadne.message.parser.twilight import FullMatch, Sparkle, Twilight
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
