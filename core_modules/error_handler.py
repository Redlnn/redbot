#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import traceback
from io import StringIO

from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.util.saya import listen
from graia.broadcast.builtin.event import ExceptionThrowed
from graia.saya import Channel

from util.config import basic_cfg
from util.text2img import Text2ImgConfig, async_generate_img

channel = Channel.current()
channel.meta['can_disable'] = False


@listen(ExceptionThrowed)
async def except_handle(event: ExceptionThrowed):
    if isinstance(event.event, ExceptionThrowed):
        return
    app = Ariadne.current()
    with StringIO() as fp:
        traceback.print_tb(event.exception.__traceback__, file=fp)
        tb = fp.getvalue()
    msg = [
        f'异常事件：\n{str(event.event)}\n'
        f'异常类型：\n{type(event.exception)}\n'
        f'异常内容：\n{str(event.exception)}\n'
        f'异常追踪：\n{tb}'
    ]
    img_bytes = await async_generate_img(msg, Text2ImgConfig(CharsPerLine=80))
    await app.send_friend_message(basic_cfg.admin.masterId, MessageChain(Plain('发生异常\n'), Image(data_bytes=img_bytes)))


# from graia.ariadne.event.message import GroupMessage
# @listen(GroupMessage)
# async def test(msg: MessageChain):
#     if msg.display == 'error_handler_test':
#         raise ValueError('test')
