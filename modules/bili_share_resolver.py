#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
识别群内的B站链接、分享、av号、BV号并获取其对应的视频的信息

以下几种消息均可触发

 - 新版B站app分享的两种小程序
 - 旧版B站app分享的xml消息
 - B站概念版分享的json消息
 - 文字消息里含有B站视频地址，如 https://www.bilibili.com/video/{av/bv号} （m.bilibili.com 也可以
 - 文字消息里含有B站视频地址，如 https://b23.tv/3V31Ap
 - 文字消息里含有B站视频地址，如 https://b23.tv/3V31Ap
 - BV1xx411c7mD
 - av2
"""

import time
from dataclasses import dataclass
from typing import Literal

import regex as re
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.model import Group, Member
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from loguru import logger

from util.control import DisableModule
from util.control.interval import ManualInterval
from util.control.permission import GroupPermission
from util.get_aiohtto_session import get_session
from util.text2img import async_generate_img, hr

channel = Channel.current()

channel.meta['name'] = 'B站视频信息获取'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = '识别群内的B站链接、分享、av号、BV号并获取其对应的视频的信息\n'
'以下几种消息均可触发：\n'
' - 新版B站app分享的两种小程序\n'
' - 旧版B站app分享的xml消息\n'
' - B站概念版分享的json消息\n'
' - 文字消息里含有B站视频地址，如 https://www.bilibili.com/video/{av/bv号} （m.bilibili.com 也可以）\n'
' - 文字消息里含有B站视频地址，如 https://b23.tv/3V31Ap\n'
' - 文字消息里含有BV号，如 BV1xx411c7mD\n'
' - 文字消息里含有av号，如 av2'

avid_re = '(av|AV)(\\d{1,12})'
bvid_re = '[Bb][Vv]1([0-9a-zA-Z]{2})4[1y]1[0-9a-zA-Z]7([0-9a-zA-Z]{2})'


@dataclass
class VideoInfo:
    cover_url: str  # 封面地址
    bvid: str  # BV号
    avid: int  # av号
    title: str  # 视频标题
    sub_count: int  # 视频分P数
    pub_timestamp: int  # 视频发布时间（时间戳）
    unload_timestamp: int  # 视频上传时间（时间戳，不一定准确）
    desc: str  # 视频简介
    duration: int  # 视频长度（单位：秒）
    up_mid: int  # up主mid
    up_name: str  # up主名称
    views: int  # 播放量
    danmu: int  # 弹幕数
    likes: int  # 点赞数
    coins: int  # 投币数
    favorites: int  # 收藏量


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage], decorators=[GroupPermission.require(), DisableModule.require(channel.module)]
    )
)
async def main(app: Ariadne, group: Group, message: MessageChain, member: Member):
    p = re.compile(f'({avid_re})|({bvid_re})')
    msg_str = message.asPersistentString()
    if 'b23.tv/' in msg_str:
        msg_str = await b23_url_extract(msg_str)
        if not msg_str:
            return
    video_id = p.search(msg_str)
    if not video_id or video_id is None:
        return
    video_id = video_id.group()

    rate_limit, remaining_time = ManualInterval.require(f'{group.id}_{member.id}_bilibiliVideoInfo', 5, 2)
    if not rate_limit:
        await app.sendMessage(group, MessageChain.create(Plain(f'冷却中，剩余{remaining_time}秒，请稍后再试')))
        return

    video_info = await get_video_info(video_id)
    if video_info['code'] == -404:
        return await app.sendMessage(group, MessageChain.create(Plain('视频不存在')))
    elif video_info['code'] != 0:
        error_text = f'解析B站视频 {video_id} 时出错👇\n错误代码：{video_info["code"]}\n错误信息：{video_info["message"]}'
        logger.error(error_text)
        return await app.sendMessage(group, MessageChain.create(Plain(error_text)))
    else:
        video_info = await info_json_dump(video_info['data'])
        img: bytes = await gen_img(video_info)
        await app.sendMessage(
            group,
            MessageChain.create(
                [
                    Image(data_bytes=img),
                    Plain(
                        f'{video_info.title}\n'
                        '————————————————————\n'
                        f'UP主：{video_info.up_name}\n'
                        f'{math(video_info.views)}播放 {math(video_info.likes)}赞\n'
                        f'链接：https://b23.tv/{video_info.bvid}'
                    ),
                ]
            ),
        )


async def b23_url_extract(b23_url: str) -> Literal[False] | str:
    url = re.search(r'b23.tv(/|\\)[0-9a-zA-Z]+', b23_url)
    if url is None:
        return False
    session = get_session()
    async with session.get(f'https://{url.group()}', allow_redirects=True) as resp:
        target = str(resp.url)
    return target if 'www.bilibili.com/video/' in target else False


async def get_video_info(video_id: str) -> dict:  # type: ignore
    session = get_session()
    if video_id[:2].lower() == 'av':
        async with session.get(f'http://api.bilibili.com/x/web-interface/view?aid={video_id[2:]}') as resp:
            return await resp.json()
    elif video_id[:2].lower() == 'bv':
        async with session.get(f'http://api.bilibili.com/x/web-interface/view?bvid={video_id}') as resp:
            return await resp.json()


async def info_json_dump(obj: dict) -> VideoInfo:
    return VideoInfo(
        cover_url=obj['pic'],
        bvid=obj['bvid'],
        avid=obj['aid'],
        title=obj['title'],
        sub_count=obj['videos'],
        pub_timestamp=obj['pubdate'],
        unload_timestamp=obj['ctime'],
        desc=obj['desc'].strip(),
        duration=obj['duration'],
        up_mid=obj['owner']['mid'],
        up_name=obj['owner']['name'],
        views=obj['stat']['view'],
        danmu=obj['stat']['danmaku'],
        likes=obj['stat']['like'],
        coins=obj['stat']['coin'],
        favorites=obj['stat']['favorite'],
    )


def math(num: int):
    if num < 10000:
        return str(num)
    elif num < 100000000:
        return ('%.2f' % (num / 10000)) + '万'
    else:
        return ('%.2f' % (num / 100000000)) + '亿'


async def gen_img(data: VideoInfo) -> bytes:
    video_length_m, video_length_s = divmod(data.duration, 60)  # 将总的秒数转换为时分秒格式
    video_length_h, video_length_m = divmod(video_length_m, 60)
    if video_length_h == 0:
        video_length = f'{video_length_m}:{video_length_s}'
    else:
        video_length = f'{video_length_h}:{video_length_m}:{video_length_s}'

    info_text = (
        f'BV号：{data.bvid}\n'
        f'av号：av{data.avid}\n'
        f'标题：{data.title}\n'
        f'UP主：{data.up_name}\n'
        f'时长：{video_length}\n'
        f'发布时间：{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data.pub_timestamp))}\n'
    )

    if data.sub_count > 1:
        info_text += f'分P数量：{data.sub_count}\n'

    info_text += (
        f'{math(data.views)}播放 {math(data.danmu)}弹幕\n'
        f'{math(data.likes)}点赞 {math(data.coins)}投币 {math(data.favorites)}收藏\n'
        f'简介：\n'
        f'{hr}\n{data.desc}'
    )

    session = get_session()
    async with session.get(data.cover_url) as resp:
        img_contents: list[str | bytes] = [await resp.content.read(), info_text]
    return await async_generate_img(img_contents)
