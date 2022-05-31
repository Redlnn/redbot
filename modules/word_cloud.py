#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
移植自：https://github.com/djkcyl/ABot-Graia/blob/MAH-V2/saya/WordCloud/__init__.py
"""

import datetime
import random
import time
from contextvars import ContextVar
from io import BytesIO
from os import listdir
from pathlib import Path

import jieba.analyse
import numpy
import regex as re
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Plain
from graia.ariadne.message.parser.twilight import (
    ArgResult,
    ArgumentMatch,
    RegexMatch,
    RegexResult,
    SpacePolicy,
    Twilight,
    UnionMatch,
    WildcardMatch,
)
from graia.ariadne.model import Group, Member
from graia.ariadne.util.async_exec import cpu_bound
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from jieba import load_userdict
from matplotlib import pyplot
from PIL import Image as Img
from wordcloud import ImageColorGenerator, WordCloud

from util.config import RConfig
from util.control import require_disable
from util.control.interval import ManualInterval
from util.control.permission import GroupPermission
from util.database.log_msg import get_group_msg, get_member_msg
from util.path import data_path

channel = Channel.current()

channel.meta['name'] = '聊天历史词云生成'
channel.meta['author'] = ['Red_lnn', 'A60(djkcyl)']
channel.meta['description'] = '获取指定目标在最近n天内的聊天词云\n用法：\n'
'  - 群/我的本周总结'
'  - 群/我的月度总结'
'  - 群/我的年度总结'
'  - [!！.]wordcloud group —— 获得本群最近n天内的聊天词云\n'
'  - [!！.]wordcloud At/本群成员QQ号 —— 获得ta在本群最近n天内的聊天词云\n'
'  - [!！.]wordcloud me —— 获得你在本群最近n天内的聊天词云\n'
'    参数：\n'
'        --day, -D 最近n天的天数，默认为7天'


class WordCloudConfig(RConfig):
    __filename__: str = 'wordcloud'
    blacklistWord: list[str] = []
    fontName: str = 'OPPOSans-B.ttf'


generating_list: ContextVar[list[int | str]] = ContextVar('generating_list', default=[])
config = WordCloudConfig()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    RegexMatch(r'[!！.]wordcloud').space(SpacePolicy.FORCE),
                    'wc_target' @ WildcardMatch(),
                    'day_length' @ ArgumentMatch('--day', '-D', default='7'),
                ],
            )
        ],
        decorators=[
            GroupPermission.require(),
            require_disable(channel.module),
            require_disable('core_modules.msg_loger'),
        ],
    )
)
async def command(app: Ariadne, group: Group, member: Member, wc_target: RegexResult, day_length: ArgResult):
    if day_length.result is None:
        return
    try:
        day = int(day_length.result)
    except ValueError:
        await app.send_message(group, MessageChain(Plain('请输入正确的天数！')), quote=True)
        return
    match_result: MessageChain = wc_target.result  # type: ignore # noqa: E275

    process_list = generating_list.get()
    if len(process_list) > 2:
        await app.send_message(group, MessageChain(Plain('词云生成队列已满，请稍后再试')))
        return

    if len(match_result) == 0:
        return
    elif match_result.display == 'group':
        result = await gen_wordcloud_group(app, group, day)
        if result is None:
            return
        else:
            await app.send_message(group, MessageChain(Plain(f'本群最近{day}天的聊天词云 👇\n'), result))
    elif match_result.display == 'me':
        result = await gen_wordcloud_member(app, group, member.id, day, True)
        if result is None:
            return
        else:
            await app.send_message(group, MessageChain(Plain(f'你最近{day}天的聊天词云 👇\n'), result))
    elif match_result.only_contains(At):
        at = match_result.get_first(At)
        result = await gen_wordcloud_member(app, group, at.target, day, False)
        if result is None:
            return
        else:
            await app.send_message(group, MessageChain(at, Plain(f' 最近{day}天的聊天词云 👇\n'), result))
    elif match_result.display.isdigit():
        target = int(match_result.display)
        result = await gen_wordcloud_member(app, group, target, day, False)
        if result is None:
            return
        else:
            await app.send_message(group, MessageChain(At(target), Plain(f' 最近{day}天的聊天词云 👇\n'), result))
    else:
        await app.send_message(group, MessageChain(Plain('参数错误，无效的命令')))
        return


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    'target' @ UnionMatch('我的', '群').space(SpacePolicy.NOSPACE),
                    'target_time' @ UnionMatch('本周总结', '月度总结', '年度总结'),
                ],
            )
        ],
        decorators=[
            GroupPermission.require(),
            require_disable(channel.module),
            require_disable('core_modules.msg_loger'),
        ],
    )
)
async def main(app: Ariadne, group: Group, member: Member, target: RegexResult, target_time: RegexResult):
    if target.result is None or target_time.result is None:
        return
    today = time.localtime(time.time())
    match target.result.display:
        case '我的':
            match target_time.result.display:
                case '本周总结':
                    result = await gen_wordcloud_member(app, group, member.id, today.tm_wday + 1, True)
                    if result is None:
                        return
                    else:
                        await app.send_message(group, MessageChain(Plain(f'你本周的聊天词云 👇\n'), result))
                case '月度总结':
                    result = await gen_wordcloud_member(app, group, member.id, today.tm_mday + 1, True)
                    if result is None:
                        return
                    else:
                        await app.send_message(group, MessageChain(Plain(f'你本月的聊天词云 👇\n'), result))
                case '年度总结':
                    result = await gen_wordcloud_member(app, group, member.id, today.tm_yday + 1, True)
                    if result is None:
                        return
                    else:
                        await app.send_message(group, MessageChain(Plain(f'你今年的聊天词云 👇\n'), result))
        case '群':
            match target_time.result.display:
                case '本周总结':
                    result = await gen_wordcloud_group(app, group, today.tm_wday + 1)
                    if result is None:
                        return
                    else:
                        await app.send_message(group, MessageChain(Plain(f'本群本周的聊天词云 👇\n'), result))
                case '月度总结':
                    result = await gen_wordcloud_group(app, group, today.tm_mday + 1)
                    if result is None:
                        return
                    else:
                        await app.send_message(group, MessageChain(Plain(f'本群本月的聊天词云 👇\n'), result))
                case '年度总结':
                    result = await gen_wordcloud_group(app, group, today.tm_yday + 1)
                    if result is None:
                        return
                    else:
                        await app.send_message(group, MessageChain(Plain(f'本群今年的聊天词云 👇\n'), result))


async def gen_wordcloud_member(app: Ariadne, group: Group, target: int, day: int, me: bool) -> None | Image:
    process_list = generating_list.get()
    if target in process_list:
        await app.send_message(
            group,
            MessageChain(Plain('你') if me else At(target), Plain('的词云已在生成中，请稍后...')),
        )
        return
    rate_limit, remaining_time = ManualInterval.require('wordcloud_member', 30, 2)
    if not rate_limit:
        await app.send_message(group, MessageChain(Plain(f'冷却中，剩余{remaining_time}秒，请稍后再试')))
        return
    process_list.append(target)
    target_timestamp = int(time.mktime(datetime.date.today().timetuple())) - (day - 1) * 86400
    msg_list = await get_member_msg(str(group.id), str(target), target_timestamp)

    if len(msg_list) < 50:
        process_list.remove(target)
        await app.send_message(
            group,
            MessageChain(Plain('你') if me else At(target), Plain('的发言较少，无法生成词云')),
        )
        return
    await app.send_message(
        group, MessageChain(Plain('你') if me else At(target), Plain(f'最近{day}天共 {len(msg_list)} 条记录，正在生成词云，请稍后...'))
    )

    words = await get_frequencies(msg_list)
    image_bytes = await gen_wordcloud(words)
    process_list.remove(target)
    generating_list.set(process_list)
    return Image(data_bytes=image_bytes)


async def gen_wordcloud_group(app: Ariadne, group: Group, day: int) -> None | Image:
    process_list = generating_list.get()
    if group.id in process_list:
        await app.send_message(group, MessageChain(Plain('本群词云已在生成中，请稍后...')))
        return
    rate_limit, remaining_time = ManualInterval.require('wordcloud_group', 300, 1)
    if not rate_limit:
        await app.send_message(group, MessageChain(Plain(f'冷却中，剩余{remaining_time}秒，请稍后再试')))
        return
    process_list.append(group.id)
    target_timestamp = int(time.mktime(datetime.date.today().timetuple())) - (day - 1) * 86400
    msg_list = await get_group_msg(str(group.id), target_timestamp)
    if len(msg_list) < 50:
        await app.send_message(group, MessageChain(Plain('本群发言较少，无法生成词云')))
        process_list.remove(group.id)
        return
    await app.send_message(group, MessageChain(Plain(f'本群最近{day}天共 {len(msg_list)} 条记录，正在生成词云，请稍后...')))
    words = await get_frequencies(msg_list)
    image_bytes = await gen_wordcloud(words)
    process_list.remove(group.id)
    generating_list.set(process_list)
    return Image(data_bytes=image_bytes)


def skip(persistent_string: str):
    return any(word in persistent_string for word in config.blacklistWord)


@cpu_bound
def get_frequencies(msg_list: list[str]) -> dict:
    text = ''
    for persistent_string in msg_list:
        if skip(persistent_string):
            continue
        tmp = re.sub(r'\[mirai:.+\]', '', persistent_string)
        text += f'{tmp}\n' if tmp else ''
    if not Path(data_path, 'WordCloud', 'user_dict.txt').exists():
        f = open(Path(data_path, 'WordCloud', 'user_dict.txt'), 'a+')
        f.close()
    load_userdict(str(Path(data_path, 'WordCloud', 'user_dict.txt')))
    words = jieba.analyse.extract_tags(text, topK=700, withWeight=True)
    return dict(words)


@cpu_bound
def gen_wordcloud(words: dict) -> bytes:
    if not Path(data_path, 'WordCloud', 'mask').exists():
        Path(data_path, 'WordCloud', 'mask').mkdir()
    elif len(listdir(Path(data_path, 'WordCloud', 'mask'))) == 0:
        raise ValueError('找不到可用的词云遮罩图，请在 data/WordCloud/mask 文件夹内放置图片文件')
    bg_list = listdir(Path(data_path, 'WordCloud', 'mask'))
    mask = numpy.array(Img.open(Path(data_path, 'WordCloud', 'mask', random.choice(bg_list))))
    font_path = str(Path(Path.cwd(), 'fonts', config.fontName))
    wordcloud = WordCloud(font_path=font_path, background_color='#f0f0f0', mask=mask, max_words=700, scale=2)
    wordcloud.generate_from_frequencies(words)
    image_colors = ImageColorGenerator(mask, default_color=(255, 255, 255))
    wordcloud.recolor(color_func=image_colors)
    # pyplot.imshow(wordcloud.recolor(color_func=image_colors), interpolation='bilinear')
    # pyplot.axis('off')
    image = wordcloud.to_image()
    imageio = BytesIO()
    image.save(imageio, format='JPEG', quality=90, optimize=True, progressive=True, subsampling=2, qtables='web_high')
    return imageio.getvalue()
