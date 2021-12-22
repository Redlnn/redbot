#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
搜索我的世界中文Wiki

用法：在群内发送【!wiki {关键词}】即可
"""

import asyncio
from os.path import basename
from random import uniform
from urllib.parse import quote

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Xml
from graia.ariadne.message.parser.twilight import RegexMatch, Sparkle, Twilight
from graia.ariadne.model import Group
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from utils.config import get_modules_config
from utils.control.interval import MemberInterval
from utils.control.permission import GroupPermission
from utils.module_register import Module

channel = Channel.current()
modules_cfg = get_modules_config()
module_name = basename(__file__)

Module(
    name='搜索我的世界中文Wiki',
    file_name=module_name,
    author=['Red_lnn'],
    usage='[!！.]wiki <要搜索的关键词>',
).register()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]wiki\ ')], {'keyword': RegexMatch(r'\S+')}))],
        decorators=[GroupPermission.require(), MemberInterval.require(3)],
    )
)
async def main(app: Ariadne, group: Group, keyword: RegexMatch):
    if module_name in modules_cfg.disabledGroups:
        if group.id in modules_cfg.disabledGroups[module_name]:
            return
    arg: str = keyword.result.asDisplay()
    search_parm: str = quote(arg, encoding='utf-8')
    bilibili_wiki = (
        '<?xml version=\'1.0\' encoding=\'UTF-8\' standalone=\'yes\'?><msg templateID="123" '
        f'url="https://searchwiki.biligame.com/mc/index.php?search={search_parm}" serviceID="33" action="web" '
        f'actionData="" brief="【链接】{arg} - Biligame Wiki" flag="8"><item layout="2">'
        '<picture cover="https://s1.hdslb.com/bfs/static/game-web/duang/mine/asserts/contact.404066f.png"/>'
        f'<title>{arg} - Biligame Wiki</title><summary>{arg} - Biligame Wiki for Minecraft，哔哩哔哩游戏</summary>'
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
    await app.sendGroupMessage(group, MessageChain.create(Xml(xml=bilibili_wiki, type='Xml')))
    await asyncio.sleep(round(uniform(0.5, 1.5), 3))
    await app.sendGroupMessage(group, MessageChain.create(Xml(xml=fandom_gamepedia_wiki, type='Xml')))
