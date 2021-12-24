#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graia.ariadne.app import Ariadne
from graia.ariadne.console.saya import ConsoleSchema
from graia.ariadne.message.parser.twilight import FullMatch, Sparkle, Twilight
from graia.saya import Channel

channel = Channel.current()


@channel.use(ConsoleSchema([Twilight(Sparkle([FullMatch('stop')]))]))
async def stop(app: Ariadne):
    await app.stop()
