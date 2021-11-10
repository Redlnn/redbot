#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform

import git
import psutil
import regex
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.model import Group
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Rate import GroupInterval
from utils.TextWithImg2Img import async_generate_img, hr

saya = Saya.current()
channel = Channel.current()

channel.name('Bot版本与系统运行情况查询')
channel.author('Red_lnn')
channel.description('用法：[!！.](status|version)')

repo = git.Repo(os.getcwd())


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                decorators=[group_blacklist(), GroupInterval.require(5, send_alert=False)],
        )
)
async def main(app: Ariadne, group: Group, message: MessageChain):
    if not regex.match(r'^[!！.](status|version)$'):
        return
    mem_info = psutil.virtual_memory()._asdict()
    msg_send = (
        '-= Red_lnn Bot 状态 =-\n\n'
        f'bot 版本：{str(repo.head.reference.commit)[:7]}-dev\n'
        f'更新日期：{repo.head.reference.commit.committed_datetime}\n'
        f'{hr}\n'
        f'Python 版本：{platform.python_version()}\n'
        f'系统版本：{platform.platform()}'
        f'系统 CPU 占用率：{psutil.cpu_percent()}%\n'
        f'系统内存占用：{"%.1f" % (mem_info["available"] / 1073741824)}G/{"%.1f" % (mem_info["total"] / 1073741824)}G\n'
    )

    img_io = await async_generate_img([msg_send])
    await app.sendGroupMessage(group, MessageChain.create(Image(data_bytes=img_io.getvalue())))
