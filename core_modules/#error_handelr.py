#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import traceback
from io import StringIO

from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.broadcast.builtin.event import ExceptionThrowed
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from utils.config import get_main_config
from utils.text2img import async_generate_img

channel = Channel.current()

basic_cfg = get_main_config()


@channel.use(ListenerSchema(listening_events=[ExceptionThrowed]))
async def except_handle(app: Ariadne, event: ExceptionThrowed):
    if isinstance(event.event, ExceptionThrowed):
        return
    else:
        with StringIO() as fp:
            traceback.print_tb(event.exception.__traceback__, file=fp)
            tb = fp.getvalue()
        msg = [
            f'异常事件：\n{str(event.event)}\n'
            f'异常类型：\n{type(event.exception)}\n'
            f'异常内容：\n{str(event.exception)}\n'
            f'异常追踪：\n{tb}'
        ]
        img_bytes = await async_generate_img(msg, 100)
        await app.sendTempMessage(
            basic_cfg.admin.masterId, MessageChain.create(Plain('发生异常\n'), Image(data_bytes=img_bytes))
        )
