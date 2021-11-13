#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform
import time

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

from config import config_data
from utils.Limit.Blacklist import group_blacklist
from utils.TextWithImg2Img import async_generate_img, hr

saya = Saya.current()
channel = Channel.current()

if not config_data['Modules']['BotStatus']['Enabled']:
    saya.uninstall_channel(channel)

channel.name('Bot版本与系统运行情况查询')
channel.author('Red_lnn')
channel.description('用法：[!！.](status|version)')

repo = git.Repo(os.getcwd())

commit = repo.head.reference.commit.hexsha
commit_date = repo.head.reference.commit.committed_datetime
python_version = platform.python_version()
if platform.uname().system == 'Windows':
    system_version = platform.platform()
else:
    system_version = f'{platform.platform()} {platform.version()}'
total_memory = '%.1f' % (psutil.virtual_memory().total / 1073741824)


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                decorators=[group_blacklist()],
        )
)
async def main(app: Ariadne, group: Group, message: MessageChain):
    if config_data['Modules']['BotStatus']['DisabledGroup']:
        if group.id in config_data['Modules']['BotStatus']['DisabledGroup']:
            return
    if not regex.match(r'^[!！.](status|version)$', message.asDisplay()):
        return
    PID = os.getpid()
    p = psutil.Process(PID)
    started_time = time.localtime(p.create_time())
    running_time = time.time() - p.create_time()
    day = int(running_time / 86400)
    hour = int(running_time % 86400 / 3600)
    minute = int(running_time % 86400 % 3600 / 60)
    second = int(running_time % 86400 % 3600 % 60)
    running_time = (
        f'{str(day) + "d " if day else ""}'
        f'{str(hour) + "h " if hour else ""}'
        f'{str(minute) + "m " if minute else ""}'
        f'{second}s'
    )
    msg_send = (
        '-= Red_lnn Bot 状态 =-\n\n'
        f'bot 版本：{commit[:7]}-dev\n'
        f'更新日期：{commit_date}\n'
        f'MiraiApiHttp版本：{await app.getVersion()}\n'
        f'PID: {PID}\n'
        f'启动时间：{time.strftime("%Y-%m-%d %H:%M:%S", started_time)}\n'
        f'已运行时长：{running_time}\n'
        f'{hr}\n'
        f'Python 版本：{python_version}\n'
        f'系统版本：{system_version}\n'
        f'CPU 核心数：{psutil.cpu_count()}\n'
        f'CPU 占用率：{psutil.cpu_percent()}%\n'
        f'系统内存占用：{"%.1f" % (psutil.virtual_memory().available / 1073741824)}G / {total_memory}G\n'
    )

    img_io = await async_generate_img([msg_send])
    await app.sendGroupMessage(group, MessageChain.create(Image(data_bytes=img_io.getvalue())))
