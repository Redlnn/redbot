#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
搜索我的世界中文Wiki

用法：在群内发送【!wiki {关键词}】即可
"""

import asyncio
import json
from random import uniform
from urllib.parse import quote

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import App
from graia.ariadne.message.parser.pattern import RegexMatch
from graia.ariadne.message.parser.twilight import Sparkle, Twilight
from graia.ariadne.model import Group
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from config import config_data
from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Rate import MemberInterval

saya = Saya.current()
channel = Channel.current()

if not config_data['Modules']['SearchMinecraftWiki']['Enabled']:
    saya.uninstall_channel(channel)

channel.name('搜索我的世界中文Wiki')
channel.author('Red_lnn')
channel.description('用法：[!！.]wiki <要搜索的关键词>')


class Match(Sparkle):
    prefix = RegexMatch(r'[!！.]wiki\ ')
    search_target = RegexMatch(r'\S+')


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(Match)],
                decorators=[group_blacklist(), MemberInterval.require(3)],
        )
)
async def main(app: Ariadne, group: Group, sparkle: Sparkle):
    if config_data['Modules']['SearchMinecraftWiki']['DisabledGroup']:
        if group.id in config_data['Modules']['SearchMinecraftWiki']['DisabledGroup']:
            return
    arg: str = sparkle.search_target.result.asDisplay()
    search_parm: str = quote(arg, encoding='utf-8')
    bilibili_wiki_json = {
        'app': 'com.tencent.structmsg',
        'desc': '新闻',
        'view': 'news',
        'ver': '0.0.0.1',
        'prompt': '',
        'meta': {
            'news': {
                'title': f'Biligame Wiki: {arg}',
                'desc': f'{arg} - Biligame Wiki for Minecraft，哔哩哔哩游戏',
                'preview': 'https://s1.hdslb.com/bfs/static/game-web/duang/mine/asserts/contact.404066f.png',
                'tag': 'Red_lnn Bot',
                'jumpUrl': f'https://searchwiki.biligame.com/mc/index.php?search={str(search_parm)}',
                'appid': 100446242,
                'app_type': 1,
                'action': '',
                'source_url': '',
                'source_icon': '',
                'android_pkg_name': '',
            }
        },
    }
    # gamepedia_wiki_json = {
    #     'app': 'com.tencent.structmsg',
    #     'desc': '新闻',
    #     'view': 'news',
    #     'ver': '0.0.0.1',
    #     'prompt': '',
    #     'meta': {
    #             'news': {
    #                 'title': f'Minecraft Wiki: {arg}',
    #                 'desc': f'{arg} - Minecraft Wiki，最详细的官方我的世界百科',
    #                 'preview': 'https://images.wikia.com/minecraft_zh_gamepedia/images/b/bc/Wiki.png',
    #                 'tag': 'Red_lnn Bot',
    #                 'jumpUrl': f'https://minecraft-zh.gamepedia.com/index.php?search={str(search_parm)}',
    #                 'appid': 100446242,
    #                 'app_type': 1,
    #                 'action': '',
    #                 'source_url': '',
    #                 'source_icon': '',
    #                 'android_pkg_name': ''
    #             }
    #         }
    # }
    fandom_gamepedia_wiki_json = {
        'app': 'com.tencent.structmsg',
        'desc': '新闻',
        'view': 'news',
        'ver': '0.0.0.1',
        'prompt': '',
        'meta': {
            'news': {
                'title': f'Minecraft Wiki: {arg}',
                'desc': f'{arg} - Minecraft Wiki，最详细的官方我的世界百科',
                'preview': 'https://images.wikia.com/minecraft_zh_gamepedia/images/b/bc/Wiki.png',
                'tag': 'Red_lnn Bot',
                'jumpUrl': f'https://minecraft.fandom.com/zh/index.php?search={str(search_parm)}',
                'appid': 100446242,
                'app_type': 1,
                'action': '',
                'source_url': '',
                'source_icon': '',
                'android_pkg_name': '',
            }
        },
    }
    await app.sendGroupMessage(group, MessageChain.create([App(content=json.dumps(bilibili_wiki_json), type='App')]))
    await asyncio.sleep(round(uniform(0.5, 1.3), 2))
    await app.sendGroupMessage(
            group, MessageChain.create([App(content=json.dumps(fandom_gamepedia_wiki_json), type='App')])
    )
