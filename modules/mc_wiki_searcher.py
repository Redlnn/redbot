#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
搜索我的世界中文Wiki

用法：在群内发送【!wiki {关键词}】即可
"""

from asyncio.exceptions import TimeoutError
from urllib.parse import quote

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.twilight import (
    RegexMatch,
    RegexResult,
    SpacePolicy,
    Twilight,
)
from graia.ariadne.model import Group
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from lxml import etree

from util.control import require_disable
from util.control.permission import GroupPermission
from util.get_aiohtto_session import get_session

channel = Channel.current()

channel.meta['name'] = '我的世界中文Wiki搜索'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = '[!！.]wiki <要搜索的关键词>'


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([RegexMatch(r'[!！.]wiki').space(SpacePolicy.FORCE)], 'keyword' @ RegexMatch(r'\S+'))
        ],
        decorators=[GroupPermission.require(), require_disable(channel.module)],
    )
)
async def main(app: Ariadne, group: Group, keyword: RegexResult):
    key_word: str = keyword.result.asDisplay().strip()  # type: ignore
    search_parm: str = quote(key_word, encoding='utf-8')

    bili_search_url = 'https://searchwiki.biligame.com/mc/index.php?search=' + search_parm
    fandom_search_url = 'https://minecraft.fandom.com/zh/index.php?search=' + search_parm

    bili_url = 'https://wiki.biligame.com/mc/' + search_parm
    fandom_url = 'https://minecraft.fandom.com/zh/wiki/' + search_parm + '?variant=zh-cn'

    session = get_session()
    try:
        async with session.get(bili_url) as resp:
            status_code = resp.status
            text = await resp.text()
    except TimeoutError:
        status_code = -1

    match status_code:
        case 404:
            msg = MessageChain.create(
                Plain(
                    f'Minecraft Wiki 没有名为【{key_word}】的页面，'
                    '要继续搜索请点击下面的链接：\n'
                    f'Bilibili 镜像: {bili_search_url}\n'
                    f'Fandom: {fandom_search_url}'
                )
            )
        case 200:
            tree = etree.HTML(text)  # type: ignore # 虽然这里缺少参数，但可以运行，文档示例也如此
            title = tree.xpath('/html/head/title')[0].text
            introduction_list: list = tree.xpath(
                '//div[contains(@id,"toc")]/preceding::p[1]/descendant-or-self::*/text()'
            )
            introduction = ''.join(introduction_list).strip()
            msg = MessageChain.create(
                Plain(f'{title}\n' f'{introduction}\n' f'Bilibili 镜像: {bili_url}\n' f'Fandom: {fandom_url}')
            )
        case _:
            msg = MessageChain.create(
                Plain(
                    f'无法查询 Minecraft Wiki，错误代码：{status_code}\n'
                    f'要继续搜索【{key_word}】请点击下面的链接：\n'
                    f'Bilibili 镜像: {bili_search_url}\n'
                    f'Fandom: {fandom_search_url}'
                )
            )

    await app.sendMessage(group, msg)
