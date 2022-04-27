#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform
import time
from os.path import basename

import psutil
from git.repo.base import Repo
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import RegexMatch, Twilight
from graia.ariadne.model import Group
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from util import get_graia_version
from util.control import DisableModule
from util.control.permission import GroupPermission
from util.module_register import Module
from util.text2img import async_generate_img, hr

channel = Channel.current()
module_name = basename(__file__)[:-3]

Module(
    name='Bot版本与系统运行情况查询',
    file_name=module_name,
    author=['Red_lnn'],
    usage='[!！.](status|version)',
    can_disable=False,
).register()

repo = Repo(os.getcwd())
official, community = get_graia_version()

commit = repo.head.reference.commit.hexsha
commit_date = repo.head.reference.commit.committed_datetime
python_version = platform.python_version()
if platform.uname().system == 'Windows':
    system_version = platform.platform()
else:
    system_version = f'{platform.platform()} {platform.version()}'
total_memory = '%.1f' % (psutil.virtual_memory().total / 1073741824)
pid = os.getpid()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.](status|version)')])],
        decorators=[GroupPermission.require(), DisableModule.require(module_name)],
    )
)
async def main(app: Ariadne, group: Group):
    p = psutil.Process(pid)
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
        f'PID: {pid}\n'
        f'启动时间：{time.strftime("%Y-%m-%d %H:%M:%S", started_time)}\n'
        f'已运行时长：{running_time}\n'
        f'{hr}\n'
        f'Python 版本：{python_version}\n'
        f'系统版本：{system_version}\n'
        f'CPU 核心数：{psutil.cpu_count()}\n'
        f'CPU 占用率：{psutil.cpu_percent()}%\n'
        f'系统内存占用：{"%.1f" % (psutil.virtual_memory().available / 1073741824)}G / {total_memory}G\n'
        f'{hr}\n'
        f'MiraiApiHttp版本：{await app.getVersion()}\n'
        'Graia 相关库版本：\n'
    )
    msg_send += ''.join(f'  graia-{name}：{version}\n' for name, version in official)
    if community:
        msg_send += ''.join(f'  graiax-{name}：{version}\n' for name, version in community)

    img_bytes = await async_generate_img([msg_send.rstrip()])
    await app.sendMessage(group, MessageChain.create(Image(data_bytes=img_bytes)))
