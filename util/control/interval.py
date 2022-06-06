#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
群、用户调用频率限制（bot主人与bot管理员可以无视，没有开关）

Xenon 管理：https://github.com/McZoo/Xenon/blob/master/lib/control.py
"""

import time
from asyncio import Lock
from collections import defaultdict
from typing import DefaultDict, Optional, Set, Tuple

from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain
from graia.ariadne.model import Group, Member
from graia.broadcast import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from .permission import GroupPermission


class GroupInterval:
    """用于管理群组调用bot的冷却的类，不应被实例化"""

    last_exec: DefaultDict[int, Tuple[int, float]] = defaultdict(lambda: (1, 0.0))
    last_alert: DefaultDict[int, float] = defaultdict(float)
    sent_alert: Set[int] = set()
    lock: Optional[Lock] = None

    @classmethod
    async def get_lock(cls):
        if not cls.lock:
            cls.lock = Lock()
        return cls.lock

    @classmethod
    def require(
        cls,
        suspend_time: float,
        max_exec: int = 1,
        send_alert: bool = True,
        alert_time_interval: int = 5,
        override_level: int = GroupPermission.ADMIN,
    ) -> Depend:
        """
        指示用户每执行 `max_exec` 次后需要至少相隔 `suspend_time` 秒才能再次触发功能
        等级在 `override_level` 以上的可以无视限制

        :param suspend_time: 冷却时间
        :param max_exec: 使用n次后进入冷却
        :param send_alert: 是否发送冷却提示
        :param alert_time_interval: 发送冷却提示时间间隔，在设定时间内不会重复警告
        :param override_level: 可超越限制的最小等级，默认为群管理员
        """

        async def cd_check(app: Ariadne, group: Group, member: Member):
            if await GroupPermission.get(member) >= override_level:
                return
            current = time.time()
            async with (await cls.get_lock()):
                last = cls.last_exec[group.id]
                if current - last[1] >= suspend_time:
                    cls.last_exec[group.id] = (1, current)
                    if group.id in cls.sent_alert:
                        cls.sent_alert.remove(group.id)
                    return
                elif last[0] < max_exec:
                    cls.last_exec[group.id] = (last[0] + 1, current)
                    if group.id in cls.sent_alert:
                        cls.sent_alert.remove(group.id)
                    return
                if send_alert:
                    if group.id not in cls.sent_alert:
                        m, s = divmod(last[1] + suspend_time - current, 60)
                        await app.send_message(
                            group, MessageChain(Plain(f'功能冷却中...\n还有{f"{str(m)}分" if m else ""}{"%d" % s}秒结束'))
                        )
                        cls.last_alert[group.id] = current
                        cls.sent_alert.add(group.id)
                    elif current - cls.last_alert[group.id] > alert_time_interval:
                        cls.sent_alert.remove(group.id)
                raise ExecutionStop()

        return Depend(cd_check)


class MemberInterval:
    """用于管理群成员调用bot的冷却的类，不应被实例化"""

    last_exec: DefaultDict[str, Tuple[int, float]] = defaultdict(lambda: (1, 0.0))
    last_alert: DefaultDict[str, float] = defaultdict(float)
    sent_alert: Set[str] = set()
    lock: Optional[Lock] = None

    @classmethod
    async def get_lock(cls):
        if not cls.lock:
            cls.lock = Lock()
        return cls.lock

    @classmethod
    def require(
        cls,
        suspend_time: float,
        max_exec: int = 1,
        send_alert: bool = True,
        alert_time_interval: int = 5,
        override_level: int = GroupPermission.ADMIN,
    ) -> Depend:
        """
        指示用户每执行 `max_exec` 次后需要至少相隔 `suspend_time` 秒才能再次触发功能
        等级在 `override_level` 以上的可以无视限制

        :param suspend_time: 冷却时间
        :param max_exec: 使用n次后进入冷却
        :param send_alert: 是否发送冷却提示
        :param alert_time_interval: 警告时间间隔，在设定时间内不会重复警告
        :param override_level: 可超越限制的最小等级，默认为群管理员
        """

        async def cd_check(app: Ariadne, group: Group, member: Member):
            if await GroupPermission.get(member) >= override_level:
                return
            current = time.time()
            name = f'{member.id}_{group.id}'
            async with (await cls.get_lock()):
                last = cls.last_exec[name]
                if current - cls.last_exec[name][1] >= suspend_time:
                    cls.last_exec[name] = (1, current)
                    if name in cls.sent_alert:
                        cls.sent_alert.remove(name)
                    return
                elif last[0] < max_exec:
                    cls.last_exec[name] = (last[0] + 1, current)
                    if member.id in cls.sent_alert:
                        cls.sent_alert.remove(name)
                    return
                if send_alert:
                    if member.id not in cls.sent_alert:
                        m, s = divmod(last[1] + suspend_time - current, 60)
                        await app.send_message(
                            group,
                            MessageChain(
                                At(member.id), Plain(f' 你在本群暂时不可调用bot，正在冷却中...\n还有{f"{m}分" if m else ""}{"%d" % s}秒结束')
                            ),
                        )
                        cls.last_alert[name] = current
                        cls.sent_alert.add(name)
                    elif current - cls.last_alert[name] > alert_time_interval:
                        cls.sent_alert.remove(name)
                raise ExecutionStop()

        return Depend(cd_check)


class ManualInterval:
    """用于管理自定义的调用bot的冷却的类，不应被实例化"""

    last_exec: DefaultDict[str, Tuple[int, float]] = defaultdict(lambda: (1, 0.0))

    @classmethod
    def require(cls, name: str, suspend_time: float, max_exec: int = 1) -> Tuple[bool, Optional[float]]:
        """
        指示用户每执行 `max_exec` 次后需要至少相隔 `suspend_time` 秒才能再次触发功能

        :param name: 需要被冷却的功能或自定义flag
        :param suspend_time: 冷却时间
        :param max_exec: 使用n次后进入冷却
        :return: True 为冷却中，False 反之，若为 False，还会返回剩余时间
        """

        current = time.time()
        last = cls.last_exec[name]
        if current - cls.last_exec[name][1] >= suspend_time:
            cls.last_exec[name] = (1, current)
            return True, None
        elif last[0] < max_exec:
            cls.last_exec[name] = (last[0] + 1, current)
            return True, None
        return False, round(last[1] + suspend_time - current, 2)
