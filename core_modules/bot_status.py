import os
import platform
import time

import psutil
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import RegexMatch, Twilight
from graia.ariadne.model import Group
from graiax.shortcut.saya import decorate, dispatch, listen
from graia.saya import Channel

from util import get_graia_version
from util.control import require_disable
from util.control.permission import GroupPermission
from util.text2img import md2img

channel = Channel.current()

channel.meta['author'] = ['Red_lnn']
channel.meta['name'] = 'Bot版本与系统运行情况查询'
channel.meta['description'] = '[!！.](status|version)'
channel.meta['can_disable'] = False

extra, official, community = get_graia_version()

python_version = platform.python_version()
if platform.uname().system == 'Windows':
    system_version = platform.platform()
else:
    system_version = f'{platform.platform()} {platform.version()}'
total_memory = '%.1f' % (psutil.virtual_memory().total / 1073741824)
pid = os.getpid()


@listen(GroupMessage)
@dispatch(Twilight(RegexMatch(r'[!！.](status|version)')))
@decorate(GroupPermission.require(), require_disable(channel.module))
async def main(app: Ariadne, group: Group):
    p = psutil.Process(pid)
    started_time = time.localtime(p.create_time())
    running_time = time.time() - p.create_time()
    day = int(running_time / 86400)
    hour = int(running_time % 86400 / 3600)
    minute = int(running_time % 86400 % 3600 / 60)
    second = int(running_time % 86400 % 3600 % 60)
    running_time = f'{f"{day}d " if day else ""}{f"{hour}h " if hour else ""}{f"{minute}m " if minute else ""}{second}s'

    md = f'''\
<div align="center">

# RedBot 状态

</div>

## 基本信息
**PID**: {pid}  
**启动时间**：{time.strftime("%Y-%m-%d %p %I:%M:%S", started_time)}  
**已运行时长**：{running_time}  

## 运行环境
**Python 版本**：{python_version}  
**系统版本**：{system_version}  
**CPU 核心数**：{psutil.cpu_count()}  
**CPU 占用率**：{psutil.cpu_percent()}%  
**系统内存占用**：{"%.1f" % (psutil.virtual_memory().available / 1073741824)}G / {total_memory}G

## 依赖版本
**Mirai Api Http**：{await app.get_version()}  
**Graia 相关**：
'''
    if extra:
        md += ''.join(f'  - {name}：{version}\n' for name, version in extra)
    md += ''.join(f'  - {name}：{version}\n' for name, version in official)
    if community:
        md += ''.join(f'  - {name}：{version}\n' for name, version in community)

    await app.send_message(group, MessageChain(Image(data_bytes=await md2img(md.rstrip()))))
