#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
搜索我的世界中文Wiki

用法：在群内发送【!wiki {关键词}】即可
"""

import asyncio
import os
from random import uniform
from urllib.parse import quote

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Xml
from graia.ariadne.message.parser.pattern import RegexMatch
from graia.ariadne.message.parser.twilight import Sparkle, Twilight
from graia.ariadne.model import Group
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from config import config_data
from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Rate import MemberInterval
from utils.ModuleRegister import Module

saya = Saya.current()
channel = Channel.current()

Module(
    name='搜索我的世界中文Wiki',
    config_name='SearchMinecraftWiki',
    file_name=os.path.basename(__file__),
    author=['Red_lnn'],
    usage='[!！.]wiki <要搜索的关键词>',
).register()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]wiki\ '), RegexMatch(r'\S+')]))],
        decorators=[group_blacklist(), MemberInterval.require(3)],
    )
)
async def main(app: Ariadne, group: Group, sparkle: Sparkle):
    if not config_data['Modules']['SearchMinecraftWiki']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['SearchMinecraftWiki']['DisabledGroup']:
        if group.id in config_data['Modules']['SearchMinecraftWiki']['DisabledGroup']:
            return
    arg: str = sparkle._check_1.result.asDisplay()
    search_parm: str = quote(arg, encoding='utf-8')
    bilibili_wiki = (
        '<?xml version=\'1.0\' encoding=\'UTF-8\' standalone=\'yes\'?><msg templateID="123" '
        f'url="https://searchwiki.biligame.com/mc/index.php?search={search_parm}" serviceID="33" action="web" '
        f'actionData="" brief="【链接】{arg} - Biligame Wiki" flag="8"><item layout="2">'
        '<picture cover="https://s1.hdslb.com/bfs/static/game-web/duang/mine/asserts/contact.404066f.png"/>'
        f'<title>{arg} - Minecraft Wiki</title><summary>{arg} - Biligame Wiki for Minecraft，哔哩哔哩游戏</summary>'
        '</item></msg>'
    )
    fandom_gamepedia_wiki = (
        '<?xml version=\'1.0\' encoding=\'UTF-8\' standalone=\'yes\'?><msg templateID="123" '
        f'url="https://minecraft.fandom.com/zh/index.php?search={search_parm}" serviceID="33" action="web" '
        f'actionData="" brief="【链接】{arg} - Minecraft Wiki" flag="8"><item layout="2">'
        '<picture cover="https://images.wikia.com/minecraft_zh_gamepedia/images/b/bc/Wiki.png"/>'
        f'<title>{arg} - Minecraft Wiki</title><summary>{arg} - Minecraft Wiki，最详细的官方我的世界百科</summary>'
        '</item></msg>'
    )
    await app.sendGroupMessage(group, MessageChain.create([Xml(xml=bilibili_wiki, type='Xml')]))
    await asyncio.sleep(round(uniform(0.5, 1.5), 3))
    await app.sendGroupMessage(group, MessageChain.create([Xml(xml=fandom_gamepedia_wiki, type='Xml')]))
