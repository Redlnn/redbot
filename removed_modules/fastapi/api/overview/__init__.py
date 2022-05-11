#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import os
import platform
import time
from random import randint

import psutil
from graia.ariadne import get_running
from graia.ariadne.app import Ariadne
from graia.saya import Saya

from ...response_model import GeneralResponse

saya = Saya.current()
pid = os.getpid()
uname = platform.uname()


def get_running_time():
    p = psutil.Process(pid)
    running_time = time.time() - p.create_time()
    if running_time > 86400:
        return {'duration': round(running_time / 86400, 2), 'unit': '天'}
    if running_time > 3600:
        return {'duration': round(running_time / 3600, 1), 'unit': '小时'}
    if running_time > 60:
        return {'duration': round(running_time / 60, 1), 'unit': '分钟'}
    return {'duration': int(running_time), 'unit': '秒'}


# ----------------------------------------


async def get_info_card():
    ariadne = get_running(Ariadne)
    joined_group_count = await ariadne.getGroupList()
    return GeneralResponse(
        data={
            'today_msg_count': 114,
            'function_called_count': 514,
            'joined_group_count': len(joined_group_count),
            'module_loaded_count': len(saya.channels.keys()),
            'running_time': get_running_time(),
        }
    )


cpu_logical_count = psutil.cpu_count(logical=True)
cpu_physical_count = psutil.cpu_count(logical=False)
memory_total: int = psutil.virtual_memory().total  # Byte


async def get_sys_info():
    if platform.uname().system.lower() == "windows":
        disk_usage = psutil.disk_usage(__file__[:2]) if __file__[2] == ":" else psutil.disk_usage("C:")
    else:
        disk_usage = psutil.disk_usage("/")
    return GeneralResponse(
        data={
            'system_type': uname.system,
            'system_release': uname.release,
            'system_version': uname.version,
            'cpu_logical_count': cpu_logical_count,
            'cpu_percent': int(psutil.cpu_percent()),  # float # 立即返回模式，因此首次返回不准
            'memory_total': round(memory_total / 1073741824, 2),  # Byte -> GByte
            'memory_percent': int(psutil.virtual_memory().percent),  # float
            'disk_percent': int(disk_usage.percent),  # float
        }
    )


async def get_function_called():
    # 获取所有模块的调用次数
    # 返回调用次数最多的前5个模块
    return GeneralResponse(
        data={
            'called': [
                {'function_name': 'test1', 'function_called_count': 123},
                {'function_name': 'test2', 'function_called_count': 456},
                {'function_name': 'test3', 'function_called_count': 789},
                {'function_name': 'test4', 'function_called_count': 12},
                {'function_name': 'test5', 'function_called_count': 345},
            ]
        }
    )


async def get_message_sent_freq():
    """获取消息发送频率
    即每三小时发送的消息数量
    """
    return GeneralResponse(
        data={
            '0:00': 0,
            '1:00': 1,
            '2:00': 2,
            '3:00': 3,
            '4:00': 4,
            '5:00': 5,
            '6:00': 6,
            '7:00': 7,
            '8:00': 8,
            '9:00': 9,
            '10:00': 10,
            '11:00': 9,
            '12:00': 8,
            '13:00': 11,
            '14:00': 12,
            '15:00': 15,
            '16:00': 18,
            '17:00': 20,
            '18:00': 16,
            '19:00': 14,
            '20:00': 10,
            '21:00': 6,
            '22:00': 3,
            '23:00': 1,
        }
    )


weekday_map = {
    1: '周一',
    2: '周二',
    3: '周三',
    4: '周四',
    5: '周五',
    6: '周六',
    7: '周日',
}


def get_siginin_count():
    today = datetime.datetime.now()
    weekday = today.isoweekday()

    return GeneralResponse(
        data={
            weekday_map[weekday - 7] if (weekday - 7) > 0 else weekday + 1: randint(0, 100),
            weekday_map[weekday - 6] if (weekday - 6) > 0 else weekday + 2: randint(0, 100),
            weekday_map[weekday - 5] if (weekday - 5) > 0 else weekday + 3: randint(0, 100),
            weekday_map[weekday - 4] if (weekday - 4) > 0 else weekday + 4: randint(0, 100),
            weekday_map[weekday - 3] if (weekday - 3) > 0 else weekday + 5: randint(0, 100),
            '昨天': randint(0, 100),
            '今天': randint(0, 100),
        }
    )
