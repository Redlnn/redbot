#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
移植自：https://github.com/djkcyl/ABot-Graia/blob/MAH-V2/saya/WordCloud/__init__.py
"""

import datetime
import os
import random
import time
from io import BytesIO
from os.path import basename
from pathlib import Path
from typing import List

import jieba.analyse
import numpy
import regex as re
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.exception import UnknownError
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Plain
from graia.ariadne.message.parser.twilight import (
    ArgumentMatch,
    RegexMatch,
    Sparkle,
    Twilight,
    WildcardMatch,
)
from graia.ariadne.model import Group, Member
from graia.ariadne.util.async_exec import cpu_bound
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from jieba import load_userdict
from matplotlib import pyplot
from PIL import Image as Img
from pydantic import BaseModel
from wordcloud import ImageColorGenerator, WordCloud

from utils.config import get_config, get_modules_config
from utils.control.interval import ManualInterval
from utils.control.permission import GroupPermission
from utils.database.msg_history import get_group_msg, get_member_msg
from utils.module_register import Module
from utils.path import data_path
from utils.send_message import safeSendGroupMessage

channel = Channel.current()
modules_cfg = get_modules_config()
module_name = basename(__file__)[:-3]

Module(
    name='聊天历史词云生成',
    file_name=module_name,
    author=['Red_lnn', 'A60(djkcyl)'],
    description='获取指定目标在最近n天内的聊天词云',
    usage=(
        '[!！.]wordcloud group —— 获得本群最近n天内的聊天词云\n'
        '[!！.]wordcloud At/本群成员QQ号 —— 获得ta在本群最近n天内的聊天词云\n'
        '[!！.]wordcloud me —— 获得你在本群最近n天内的聊天词云\n'
        '参数：\n'
        '    --day, -D 最近n天的天数，默认为7天'
    ),
).register()


class WordCloudConfig(BaseModel):
    blacklistWord: List[str] = ['[APP消息]', '[XML消息]', '[JSON消息]', '视频短片']
    fontName: str = 'OPPOSans-B.ttf'


Generating_list: List[int | str] = []
config: WordCloudConfig = get_config('wordcloud.json', WordCloudConfig())


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                Sparkle(
                    [RegexMatch(r'[!！.]wordcloud')],
                    {
                        'wc_target': WildcardMatch(),
                        'day_length': ArgumentMatch('--day', '-D', regex=r'\d+', default='7'),
                    },
                )
            )
        ],
        decorators=[GroupPermission.require()],
    )
)
async def main(app: Ariadne, group: Group, member: Member, wc_target: WildcardMatch, day_length: ArgumentMatch):
    if 'LogMsgHistory' in modules_cfg.disabledGroups:
        if group.id in modules_cfg.disabledGroups['LogMsgHistory']:
            return
    elif module_name in modules_cfg.disabledGroups:
        if group.id in modules_cfg.disabledGroups[module_name]:
            return
    global Generating_list
    target_type = 'member'
    target_timestamp = (
        int(time.mktime(datetime.date.today().timetuple())) - (int(day_length.result.asDisplay()) - 1) * 86400
    )
    match_result: MessageChain = wc_target.result  # noqa: E275

    if len(Generating_list) > 2:
        await app.sendGroupMessage(group, MessageChain.create(Plain('词云生成队列已满，请稍后再试')))
        return

    if len(match_result) == 0:
        return
    elif match_result.asDisplay() == 'group':
        target_type = 'group'
        target = group.id
        if target in Generating_list:
            await app.sendGroupMessage(group, MessageChain.create(Plain('目标已在生成词云中，请稍后')))
            return
        rate_limit, remaining_time = ManualInterval.require(f'wordcloud_{target}', 600, 1)
        if not rate_limit:
            await app.sendGroupMessage(group, MessageChain.create(Plain(f'冷却中，剩余{remaining_time}秒，请稍后再试')))
            return
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
            await app.sendGroupMessage(group, MessageChain.create(Plain(f'冷却中，剩余{remaining_time}秒，请稍后再试')))
            return
        Generating_list.append(target)
        msg_list = await get_member_msg(group.id, target, target_timestamp)
    elif match_result.onlyContains(At):
        target = match_result.getFirst(At).target
        if target in Generating_list:
            await app.sendGroupMessage(group, MessageChain.create(Plain('目标已在生成词云中，请稍后')))
            return
        rate_limit, remaining_time = ManualInterval.require('wordcloud_member', 30, 2)
        if not rate_limit:
            await app.sendGroupMessage(group, MessageChain.create(Plain(f'冷却中，剩余{remaining_time}秒，请稍后再试')))
            return
        Generating_list.append(target)
        msg_list = await get_member_msg(group.id, target, target_timestamp)
    elif match_result.asDisplay().isdigit():
        target = int(match_result.asDisplay())
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

    await app.sendGroupMessage(
        group,
        MessageChain.create(
            Plain(f'正在为 {target} 生成词云，其最近{day_length.result.asDisplay()}天共 {len(msg_list)} 条记录，请稍后...')
        ),
    )
    words = await get_frequencies(msg_list)
    image_bytes = await gen_wordcloud(words)

    if target_type == 'group':
        try:
            await app.sendGroupMessage(
                group,
                MessageChain.create(
                    Plain(f'本群最近{day_length.result.asDisplay()}天内的聊天词云 👇\n'), Image(data_bytes=image_bytes)
                ),
            )
        except UnknownError:
            await app.sendGroupMessage(group, MessageChain.create(Plain('词云发送失败')))
        finally:
            Generating_list.remove(target)
    else:
        try:
            await safeSendGroupMessage(
                group,
                MessageChain.create(
                    At(target),
                    Plain(f' {"你" if target_type == "me" else ""}最近{day_length.result.asDisplay()}天内的聊天词云 👇\n'),
                    Image(data_bytes=image_bytes),
                ),
            )
        except UnknownError:
            await app.sendGroupMessage(group, MessageChain.create(Plain('词云发送失败')))
        finally:
            Generating_list.remove(target)


def skip(persistent_string: str):
    for word in config.blacklistWord:
        if word in persistent_string:
            return True
    return False


@cpu_bound
def get_frequencies(msg_list: List[str]) -> dict:
    text = ''
    for persistent_string in msg_list:
        if skip(persistent_string):
            continue
        text += re.sub(r'\[mirai:.+\]', '', persistent_string)
        text += '\n'
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
    elif len(os.listdir(Path(data_path, 'WordCloud', 'mask'))) == 0:
        raise ValueError('找不到可用的词云遮罩图，请在 data/WordCloud/mask 文件夹内放置图片文件')
    bg_list = os.listdir(Path(data_path, 'WordCloud', 'mask'))
    mask = numpy.array(Img.open(Path(data_path, 'WordCloud', 'mask', random.choice(bg_list))))
    font_path = str(Path(Path.cwd(), 'fonts', config.fontName))
    wordcloud = WordCloud(font_path=font_path, background_color='#f0f0f0', mask=mask, max_words=700, scale=2)
    wordcloud.generate_from_frequencies(words)
    image_colors = ImageColorGenerator(mask, default_color=(255, 255, 255))
    wordcloud.recolor(color_func=image_colors)
    pyplot.imshow(wordcloud.recolor(color_func=image_colors), interpolation='bilinear')
    pyplot.axis('off')
    image = wordcloud.to_image()
    imageio = BytesIO()
    image.save(imageio, format='JPEG', quality=90, optimize=True, progressive=True, subsampling=2, qtables='web_high')
    return imageio.getvalue()