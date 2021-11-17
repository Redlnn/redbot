#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
移植自：https://github.com/djkcyl/ABot-Graia/blob/MAH-V2/saya/WordCloud/__init__.py
"""

import asyncio
import datetime
import os
import random
import time
from io import BytesIO
from typing import List

import jieba.analyse
import numpy
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.exception import UnknownError, UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Plain
from graia.ariadne.message.parser.pattern import RegexMatch
from graia.ariadne.message.parser.twilight import Sparkle, Twilight
from graia.ariadne.model import Group, Member
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger
from matplotlib import pyplot
from PIL import Image as Img
from wordcloud import ImageColorGenerator, WordCloud

from config import config_data
from utils.Database.msg_history import get_group_msg, get_member_msg
from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Rate import ManualInterval
from utils.ModuleRegister import Module

saya = Saya.current()
channel = Channel.current()

Module(
    name='聊天历史词云生成',
    config_name='WordCloud',
    file_name=os.path.dirname(__file__),
    author=['Red_lnn', 'A60(djkcyl)'],
    description='获取指定目标在最近7天内的聊天词云',
    usage=(
        '[!！.]wordcloud groud —— 获得本群最近7天内的聊天词云\n'
        '[!！.]wordcloud At/本群成员QQ号 —— 获得ta在本群最近7天内的聊天词云\n'
        '[!！.]wordcloud me —— 获得你在本群最近7天内的聊天词云\n'
    ),
).register()

Generating_list: List[int | str] = []


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]wordcloud\ '), RegexMatch(r'.+')]))],
        decorators=[group_blacklist()],
    )
)
async def main(app: Ariadne, group: Group, member: Member, sparkle: Sparkle):
    if not config_data['Modules']['WordCloud']['Enabled']:
        saya.uninstall_channel(channel)
        return
    else:
        if config_data['Modules']['LogMsgHistory']['DisabledGroup']:
            if group.id in config_data['Modules']['LogMsgHistory']['DisabledGroup']:
                return
        elif config_data['Modules']['WordCloud']['DisabledGroup']:
            if group.id in config_data['Modules']['WordCloud']['DisabledGroup']:
                return
    global Generating_list
    target_type = 'member'
    target_timestamp = int(time.mktime(datetime.date.today().timetuple())) - 518400
    match_result = sparkle._check_1.result

    if len(Generating_list) > 2:
        await app.sendGroupMessage(group, MessageChain.create(Plain('词云生成队列已满，请稍后再试')))
        return

    if match_result.asDisplay() == 'group':
        target_type = 'group'
        target = group.id
        if target in Generating_list:
            await app.sendGroupMessage(group, MessageChain.create(Plain('目标已在生成词云中，请稍后')))
            return
        rate_limit, remaining_time = ManualInterval.require(f'wordcloud_{target}', 600, 1)
        if not rate_limit:
            await app.sendGroupMessage(group, MessageChain.create(Plain(f'冷却中，剩余{remaining_time}秒，请稍后')))
        Generating_list.append(target)
        msg_list = await get_group_msg(group.id, target_timestamp)
    elif match_result.asDisplay() == 'me':
        target_type = 'me'
        target = member.id
        if target in Generating_list:
            await app.sendGroupMessage(group, MessageChain.create(Plain('目标已在生成词云中，请稍后')))
            return
        rate_limit, remaining_time = ManualInterval.require('wordcloud_member', 30, 2)
        if not rate_limit:
            await app.sendGroupMessage(group, MessageChain.create(Plain(f'冷却中，剩余{remaining_time}秒，请稍后')))
        Generating_list.append(target)
        msg_list = await get_member_msg(group.id, target, target_timestamp)
    elif match_result.onlyContains(At):
        target = match_result.getFirst(At).target
        if target in Generating_list:
            await app.sendGroupMessage(group, MessageChain.create(Plain('目标已在生成词云中，请稍后')))
            return
        rate_limit, remaining_time = ManualInterval.require('wordcloud_member', 30, 2)
        if not rate_limit:
            await app.sendGroupMessage(group, MessageChain.create(Plain(f'冷却中，剩余{remaining_time}秒，请稍后')))
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

    if len(msg_list) < 50:
        await app.sendGroupMessage(group, MessageChain.create(Plain(f'目标 {target} 的样本数量较少，无法生成词云')))
        Generating_list.remove(target)
        return

    await app.sendGroupMessage(group, MessageChain.create(Plain(f'正在为 {target} 生成词云，其本周共 {len(msg_list)} 条记录，请稍后...')))
    words = await asyncio.to_thread(get_frequencies, msg_list)
    image = await asyncio.to_thread(gen_wordcloud, words)

    if target_type == 'group':
        try:
            await app.sendGroupMessage(group, MessageChain.create(Plain('本群最近7天内的聊天词云 👇\n'), Image(data_bytes=image)))
        except UnknownError:
            await app.sendGroupMessage(group, MessageChain.create(Plain('词云发送失败')))
        finally:
            Generating_list.remove(target)
    else:
        try:
            await app.sendGroupMessage(
                group,
                MessageChain.create(
                    At(target),
                    Plain(f' {"你" if target_type == "me" else ""}最近7天内的聊天词云 👇\n'),
                    Image(data_bytes=image),
                ),
            )
        except UnknownTarget:
            await app.sendGroupMessage(
                group,
                MessageChain.create(
                    Plain(f'{"你" if target_type == "me" else target} 最近7天内的聊天词云 👇\n'), Image(data_bytes=image)
                ),
            )
        except UnknownError:
            await app.sendGroupMessage(group, MessageChain.create(Plain('词云发送失败')))
        finally:
            Generating_list.remove(target)


def skip(string: str) -> bool:
    blacklist_word = (
        config_data['Modules']['WordCloud']['BlacklistWord']
        if config_data['Modules']['WordCloud']['BlacklistWord']
        else ()
    )
    for word in blacklist_word:
        if word in string:
            return True
    return False


def get_frequencies(msg_list: List[str]) -> dict:
    text = ''
    for persistent_string in msg_list:
        if skip(persistent_string):
            continue
        try:
            chain = MessageChain.fromPersistentString(persistent_string).include(Plain)
        except Exception as e:
            logger.error(f'处理该消息时出错: {persistent_string}')
            logger.exception(e)
            continue
        if len(chain) == 0:
            continue
        else:
            text += chain.asDisplay()
            text += '\n'
    jieba.load_userdict(os.path.join(os.path.dirname(__file__), 'user_dict.txt'))
    words = jieba.analyse.extract_tags(text, topK=600, withWeight=True)
    return dict(words)


def gen_wordcloud(words: dict) -> bytes:
    bg_list = os.listdir(os.path.join(os.path.dirname(__file__), 'bg'))
    mask = numpy.array(
        Img.open(os.path.join(os.path.dirname(__file__), 'bg', bg_list[random.randint(0, len(bg_list) - 1)]))
    )
    font_path = os.path.join(os.getcwd(), 'fonts', config_data['Modules']['WordCloud']['FontName'])
    wordcloud = WordCloud(font_path=font_path, background_color="white", mask=mask, max_words=600, scale=2)
    wordcloud.generate_from_frequencies(words)
    image_colors = ImageColorGenerator(mask, default_color=(255, 255, 255))
    wordcloud.recolor(color_func=image_colors)
    pyplot.imshow(wordcloud.recolor(color_func=image_colors), interpolation="bilinear")
    pyplot.axis("off")
    image = wordcloud.to_image()
    imageio = BytesIO()
    image.save(imageio, format="JPEG", quality=98)
    return imageio.getvalue()
