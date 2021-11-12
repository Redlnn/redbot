#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
群、用户黑名单：https://github.com/djkcyl/ABot-Graia/blob/MAH-V2/util/UserBlock.py
"""

from typing import Optional, Tuple

from graia.ariadne.model import Friend, Group, Member
from graia.broadcast.builtin.decorators import Depend
from graia.broadcast.exceptions import ExecutionStop

from config import config_data

__all__ = ['group_blacklist', 'friend_blacklist', 'manual_blacklist']

_blacklist_groups = config_data['Basic']['Blacklist']['Groups'] if config_data['Basic']['Blacklist']['Groups'] else []
_blacklist_users = config_data['Basic']['Blacklist']['Users'] if config_data['Basic']['Blacklist']['Users'] else []


def group_blacklist() -> Depend:
    """
    群组黑名单（可用于临时会话发起群组限制）

    在黑名单內的群组和用戶，机器人将会始终忽略
    """

    async def _check(group: Group, member: Member):
        if group.id in _blacklist_groups or member.id in _blacklist_users:
            raise ExecutionStop()

    return Depend(_check)


def friend_blacklist() -> Depend:
    """
    用户黑名单

    在黑名单內的用戶，机器人将会始终忽略
    """

    async def _check(friend: Friend):
        if friend.id in _blacklist_users:
            raise ExecutionStop()

    return Depend(_check)


def manual_blacklist(member_id: Optional[Tuple[int]], group_id: Optional[Tuple[int]]):
    """
    手动设置黑名单

    当 `group_blacklist()` 或 `friend_blacklist()` 无法使用时可用此方法
    """
    if member_id and group_id:
        if group_id in _blacklist_groups or member_id in _blacklist_users:
            raise ExecutionStop()
    elif member_id and not group_id:
        if member_id in _blacklist_users:
            raise ExecutionStop()
    elif group_id and not member_id:
        if group_id in _blacklist_users:
            raise ExecutionStop()
