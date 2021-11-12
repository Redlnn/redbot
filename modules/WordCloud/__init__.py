#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
移植自：https://github.com/djkcyl/ABot-Graia/blob/MAH-V2/saya/WordCloud/__init__.py
"""

import datetime
import os
import time
from io import BytesIO
from typing import List

import jieba.analyse
import numpy
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Plain
from graia.ariadne.message.parser.pattern import RegexMatch
from graia.ariadne.message.parser.twilight import Sparkle, Twilight
from graia.ariadne.model import Group, Member
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from matplotlib import pyplot
from PIL import Image as Img
from wordcloud import ImageColorGenerator, WordCloud

from utils.Database.msg_history import get_group_msg, get_member_msg
from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Rate import GroupInterval

channel = Channel.current()

channel.name('聊天历史词云生成')
channel.author('Red_lnn')
channel.author('A60(djkcyl)')
channel.description(
        '用法：\n'
        '[!！.]wordcloud groud —— 获得本群最近7天内的聊天词云\n'
        '[!！.]wordcloud At/本群成员QQ号 —— 获得ta最近7天内的聊天词云\n'
        '[!！.]wordcloud me —— 获得你最近7天内的聊天词云\n'
)

Generating_list: List[int | str] = []
MASK = numpy.array(Img.open(os.path.join(os.path.dirname(__file__), 'bg.jpg')))
FONT_PATH = os.path.join(os.getcwd(), 'fonts', 'OPPOSans.ttf')


class WordCloudMatch(Sparkle):
    prefix = RegexMatch(r'[!！.]wordcloud\ ')
    any = RegexMatch(r'.+')


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(WordCloudMatch)],
                decorators=[group_blacklist(), GroupInterval.require(10)],
        )
)
async def get_msg_count(app: Ariadne, group: Group, member: Member, sparkle: Sparkle):
    global Generating_list
    target_type = 'member'
    target_timestamp = int(time.mktime(datetime.date.today().timetuple())) - 518400
    match_result = sparkle.any.result

    if len(Generating_list) > 3:
        await app.sendGroupMessage(group, MessageChain.create(Plain('词云生成队列已满，请稍后再试')))
        return

    if match_result.asDisplay() == 'group':
        target_type = 'group'
        target = group.id
        if target in Generating_list:
            await app.sendGroupMessage(group, MessageChain.create(Plain('目标已在生成词云中，请稍后')))
            return
        Generating_list.append(target)
        msg_list = await get_group_msg(group.id, target_timestamp)
    elif match_result.asDisplay() == 'me':
        target_type = 'me'
        target = member.id
        if target in Generating_list:
            await app.sendGroupMessage(group, MessageChain.create(Plain('目标已在生成词云中，请稍后')))
            return
        Generating_list.append(target)
        msg_list = await get_member_msg(group.id, target, target_timestamp)
    elif match_result.onlyContains(At):
        target = match_result.getFirst(At).target
        if target in Generating_list:
            await app.sendGroupMessage(group, MessageChain.create(Plain('目标已在生成词云中，请稍后')))
            return
        Generating_list.append(target)
        msg_list = await get_member_msg(group.id, target, target_timestamp)
    elif match_result.asDisplay().isdigit():
        target = match_result.asDisplay()
        if target in Generating_list:
            await app.sendGroupMessage(group, MessageChain.create(Plain('目标已在生成词云中，请稍后')))
            return
        Generating_list.append(target)
        msg_list = await get_member_msg(group.id, target, target_timestamp)
    else:
        await app.sendGroupMessage(group, MessageChain.create(Plain('无效的命令，参数错误')))
        return

    if len(msg_list) < 10:
        await app.sendGroupMessage(group, MessageChain.create(Plain(f'目标 {target} 的样本数量较少，无法生成词云')))
        Generating_list.remove(target)
        return

    await app.sendGroupMessage(group, MessageChain.create(Plain(f'正在为 {target} 生成词云，其本周共 {len(msg_list)} 条记录，请稍后')))
    words = await get_frequencies(msg_list)
    image = await gen_wordcloud(words)
    Generating_list.remove(target)
    if target_type == 'group':
        await app.sendGroupMessage(group, MessageChain.create(Plain('本群最近7天内的聊天词云 👇\n'), Image(data_bytes=image)))
    elif target_type == 'me':
        await app.sendGroupMessage(
                group, MessageChain.create(At(target), Plain('你最近7天内的聊天词云 👇\n'), Image(data_bytes=image))
        )
    else:
        try:
            await app.sendGroupMessage(
                    group,
                    MessageChain.create(At(target), Plain(f'({target}) 最近7天内的聊天词云 👇\n'), Image(data_bytes=image))
            )
        except UnknownTarget:
            await app.sendGroupMessage(
                    group, MessageChain.create(Plain(f'{target} 最近7天内的聊天词云 👇\n'), Image(data_bytes=image))
            )


async def get_frequencies(msg_list: List[MessageChain]) -> dict:
    text = ''
    for chain in msg_list:
        chain = chain.include(Plain)
        if len(chain) == 0:
            continue
        else:
            text += chain.asDisplay()
            text += '\n'
    words = jieba.analyse.extract_tags(text, topK=800, withWeight=True)
    return dict(words)


async def gen_wordcloud(words: dict) -> bytes:
    wordcloud = WordCloud(font_path=FONT_PATH, background_color="white", mask=MASK, max_words=800, scale=2)
    wordcloud.generate_from_frequencies(words)
    image_colors = ImageColorGenerator(MASK, default_color=(255, 255, 255))
    wordcloud.recolor(color_func=image_colors)
    pyplot.imshow(wordcloud.recolor(color_func=image_colors), interpolation="bilinear")
    pyplot.axis("off")
    image = wordcloud.to_image()
    imageio = BytesIO()
    image.save(imageio, format="JPEG", quality=98)
    return imageio.getvalue()
