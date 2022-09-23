#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
搜索我的世界中文Wiki

用法：在群内发送【!wiki {关键词}】即可
"""

from asyncio.exceptions import TimeoutError
from urllib.parse import quote

from graia.amnesia.builtins.aiohttp import AiohttpClientInterface
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
from graia.ariadne.util.saya import decorate, dispatch, listen
from graia.saya import Channel
from launart import Launart
from lxml import etree

from util.control import require_disable
from util.control.permission import GroupPermission

channel = Channel.current()

channel.meta['name'] = '我的世界中文Wiki搜索'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = '[!！.]wiki <要搜索的关键词>'


@listen(GroupMessage)
@dispatch(Twilight(RegexMatch(r'[!！.]wiki').space(SpacePolicy.FORCE), 'keyword' @ RegexMatch(r'\S+')))
@decorate(GroupPermission.require(), require_disable(channel.module))
async def main(app: Ariadne, group: Group, keyword: RegexResult):
    if keyword.result is None:
        return
    key_word: str = str(keyword.result).strip()
    search_parm: str = quote(key_word, encoding='utf-8')

    bili_search_url = 'https://searchwiki.biligame.com/mc/index.php?search=' + search_parm
    fandom_search_url = 'https://minecraft.fandom.com/zh/index.php?search=' + search_parm

    bili_url = 'https://wiki.biligame.com/mc/' + search_parm
    fandom_url = 'https://minecraft.fandom.com/zh/wiki/' + search_parm + '?variant=zh-cn'

    launart = Launart.current()
    session = launart.get_interface(AiohttpClientInterface).service.session

    try:
        async with session.get(bili_url) as resp:
            status_code = resp.status
            text = await resp.text()
    except TimeoutError:
        status_code = -1

    match status_code:
        case 404:
            msg = MessageChain(
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
            msg = MessageChain(Plain(f'{title}\n{introduction}\nBilibili 镜像: {bili_url}\nFandom: {fandom_url}'))
        case _:
            msg = MessageChain(
                Plain(
                    f'无法查询 Minecraft Wiki，错误代码：{status_code}\n'
                    f'要继续搜索【{key_word}】请点击下面的链接：\n'
                    f'Bilibili 镜像: {bili_search_url}\n'
                    f'Fandom: {fandom_search_url}'
                )
            )

    await app.send_message(group, msg)
