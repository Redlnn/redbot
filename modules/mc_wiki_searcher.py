#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
搜索我的世界中文Wiki

用法：在群内发送【!wiki {关键词}】即可
"""

from os.path import basename
from urllib.parse import quote

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.twilight import RegexMatch, Sparkle, Twilight
from graia.ariadne.model import Group
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from util.config import get_modules_config
from util.control.interval import MemberInterval
from util.control.permission import GroupPermission
from util.module_register import Module

channel = Channel.current()
modules_cfg = get_modules_config()
module_name = basename(__file__)[:-3]

Module(
    name='我的世界中文Wiki搜索',
    file_name=module_name,
    author=['Red_lnn'],
    usage='[!！.]wiki <要搜索的关键词>',
).register()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]wiki')], {'keyword': RegexMatch(r'\S+')}))],
        decorators=[GroupPermission.require(), MemberInterval.require(3)],
    )
)
async def main(app: Ariadne, group: Group, keyword: RegexMatch):
    if module_name in modules_cfg.disabledGroups:
        if group.id in modules_cfg.disabledGroups[module_name]:
            return
    keyword: str = keyword.result.asDisplay()
    search_parm: str = quote(keyword, encoding='utf-8')
    await app.sendMessage(
        group,
        MessageChain.create(
            Plain(
                f'在 Minecraft Wiki 中搜索【{keyword}】\n'
                f'Bilibili 镜像: https://searchwiki.biligame.com/mc/index.php?search={search_parm}\n'
                f'Fandom: https://minecraft.fandom.com/zh/index.php?search={search_parm}'
            )
        ),
    )
