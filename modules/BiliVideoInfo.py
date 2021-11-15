#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
识别群内的B站链接、分享、av号、BV号并获取其对应的视频的信息

以下几种消息均可触发

 - 新版B站app分享的两种小程序
 - 旧版B站app分享的xml消息
 - B站概念版分享的json消息
 - 文字消息里含有B站视频地址，如 https://www.bilibili.com/video/av2
 - 文字消息里含有B站视频地址，如 https://www.bilibili.com/video/BV1xx411c7mD
 - 文字消息里含有B站视频地址，如 https://b23.tv/3V31Ap
 - BV1xx411c7mD
 - av2
"""

import json
import os
import time
from dataclasses import dataclass
from io import BytesIO
from xml.dom.minidom import parseString

import httpx
import regex
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import App, Image, Plain, Xml
from graia.ariadne.model import Group, Member
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast.schema import ListenerSchema
from loguru import logger

from config import config_data
from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Rate import ManualInterval
from utils.ModuleRegister import Module
from utils.TextWithImg2Img import async_generate_img, hr

saya = Saya.current()
channel = Channel.current()

Module(
    name='B站视频信息获取',
    config_name='BiliVideoInfo',
    file_name=os.path.basename(__file__),
    author=['Red_lnn'],
    description='识别群内的B站链接、分享、av号、BV号并获取其对应的视频的信息',
    usage=(
        '以下几种消息均可触发：\n'
        ' - 新版B站app分享的两种小程序\n'
        ' - 旧版B站app分享的xml消息\n'
        ' - B站概念版分享的json消息\n'
        ' - 文字消息里含有B站视频地址，如 https://www.bilibili.com/video/av2\n'
        ' - 文字消息里含有B站视频地址，如 https://www.bilibili.com/video/BV1xx411c7mD\n'
        ' - 文字消息里含有B站视频地址，如 https://b23.tv/3V31Ap\n'
        ' - 文字消息里含有BV号，如 BV1xx411c7mD\n'
        ' - 文字消息里含有av号，如 av2'
    ),
).register()

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


@channel.use(ListenerSchema(listening_events=[GroupMessage], decorators=[group_blacklist()]))
async def main(app: Ariadne, group: Group, message: MessageChain, member: Member):
    if not config_data['Modules']['BiliVideoInfo']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['BiliVideoInfo']['DisabledGroup']:
        if group.id in config_data['Modules']['BiliVideoInfo']['DisabledGroup']:
            return
    p = regex.compile(f'({avid_re})|({bvid_re})')
    video_id = None
    if message.has(App):
        bli_url = await lite_app_extract(message.get(App)[0])
        if not bli_url:
            return
        video_id = p.search(bli_url)
    elif message.has(Xml):
        bli_url = await xml_extract(message.get(Xml)[0])
        if not bli_url:
            return
        video_id = p.search(bli_url)
    elif message.has(Plain):
        msg = message.asDisplay().strip()
        if 'b23.tv/' in msg:
            bli_url = await b23_url_extract(msg)
            if not bli_url:
                return
            video_id = p.search(bli_url)
        elif 'www.bilibili.com/video/' in msg:
            video_id = p.search(msg)
        elif msg[:2].lower() in ('av', 'bv'):
            video_id = p.match(msg)
        else:
            return
    if not video_id:
        return

    interval_status = ManualInterval.require(f'{group.id}_{member.id}_bilibiliVideoInfo', 5, 2, False)
    if not interval_status:
        await app.sendGroupMessage(group, MessageChain.create(Plain('冷却中，请稍后再试')))
        return

    video_info = await get_video_info(video_id.group(0))
    if video_info['code'] == -404:
        return await app.sendGroupMessage(group, MessageChain.create([Plain('视频不存在')]))
    elif video_info['code'] != 0:
        error_text = (
            f'在请求 {video_id.group(0)} 的视频信息时，B站服务器返回错误：↓\n错误代码：{video_info["code"]}\n错误信息：{video_info["message"]}'
        )
        logger.error(error_text)
        return await app.sendGroupMessage(group, MessageChain.create([Plain(error_text)]))
    else:
        video_info = await info_json_dump(video_info['data'])
        img: BytesIO = await gen_img(video_info)
        await app.sendGroupMessage(
            group,
            MessageChain.create(
                [
                    Image(data_bytes=img.getvalue()),
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


async def xml_extract(xml: Xml) -> bool | str:
    xml_tree = parseString(xml.xml)
    xml_collection = xml_tree.documentElement
    if not xml_collection.hasAttribute('url'):
        return False
    xml_url = xml_collection.getAttribute('url')
    if 'www.bilibili.com/video/' in xml_url:
        return xml_url
    elif 'b23.tv/' in xml_url:
        return await b23_url_extract(xml_url)
    return False


async def lite_app_extract(app: App) -> bool | str:
    app_dict = json.loads(app.content)
    try:
        app_id = app_dict['meta']['detail_1']['appid']
    except KeyError:
        try:
            app_id = app_dict['meta']['news']['appid']
        except:  # noqa
            return False
    except:  # noqa
        return False

    if int(app_id) == 1109937557:
        b23_url = app_dict['meta']['detail_1']['qqdocurl']
        return await b23_url_extract(b23_url)
    elif int(app_id) in (1105517988, 100951776):
        b23_url = app_dict['meta']['news']['jumpUrl']
        return await b23_url_extract(b23_url)
    return False


async def b23_url_extract(url: str) -> bool | str:
    url = regex.search('b23.tv/[0-9a-zA-Z]*', url).group(0)
    async with httpx.AsyncClient(proxies={}) as client:
        resp = await client.get(f'https://{url}', follow_redirects=False)
        target = resp.headers['Location']
        if 'www.bilibili.com/video/' in target:
            return target
        else:
            return False


async def get_video_info(video_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        if video_id[:2].lower() == 'av':
            res = await client.get(f'http://api.bilibili.com/x/web-interface/view?aid={video_id[2:]}')
            return res.json()
        elif video_id[:2].lower() == 'bv':
            res = await client.get(f'http://api.bilibili.com/x/web-interface/view?bvid={video_id}')
            return res.json()


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


async def gen_img(data: VideoInfo) -> BytesIO:
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

    cover_img_bytes = httpx.get(data.cover_url).content
    cover_img_io = BytesIO(cover_img_bytes)
    img_contents = [cover_img_io, info_text]
    return await async_generate_img(img_contents)
