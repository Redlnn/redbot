#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
权限即黑名单检查

移植自 Xenon：https://github.com/McZoo/Xenon/blob/master/lib/control.py
"""

from typing import List

from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain
from graia.ariadne.model import Friend, Group, Member, MemberPerm
from graia.broadcast import ExecutionStop
from graia.broadcast.builtin.decorators import Depend
from pydantic import BaseModel

from utils.send_message import safeSendGroupMessage

from ..config import get_config, get_main_config

__all__ = ['BlacklistConfig', 'blacklist_cfg', 'Permission', 'GroupPermission', 'TempPermission', 'FriendPermission']


class BlacklistConfig(BaseModel):
    groups: List[int] = []
    users: List[int] = []


basic_cfg = get_main_config()
blacklist_cfg: BlacklistConfig = get_config('blacklist.json', BlacklistConfig())


class Permission:
    """
    用于管理权限的类，不应被实例化

    适用于群消息和来自群的临时会话
    """

    BOT_MASTER: int = 100  # Bot主人
    BOT_ADMIN: int = 90  # Bot管理员
    OWNER: int = 30  # 群主
    ADMIN: int = 20  # 群管理员
    USER: int = 10  # 群成员/好友
    BANED: int = 0  # Bot黑名单成员
    DEFAULT: int = USER

    _levels = {
        MemberPerm.Member: USER,
        MemberPerm.Administrator: ADMIN,
        MemberPerm.Owner: OWNER,
    }

    @classmethod
    async def get(cls, target: Member | Friend, allow_override: bool = True) -> int:
        """
        获取用户的权限等级

        :param target: Friend 或 Member 实例
        :param allow_override: 是否允许bot主任无视权限控制
        :return: 等级，整数
        """
        if allow_override:
            if target.id == basic_cfg.admin.masterId:
                return cls.BOT_MASTER
            elif target.id in basic_cfg.admin.admins:
                return cls.BOT_ADMIN
        if isinstance(target, Member):
            match target.permission:
                case MemberPerm.Owner:
                    return cls.OWNER
                case MemberPerm.Administrator:
                    return cls.ADMIN
                case MemberPerm.Member:
                    return cls.USER
                case _:
                    return cls.DEFAULT
        else:
            return cls.DEFAULT


class GroupPermission(Permission):
    @classmethod
    def require(
        cls,
        perm: MemberPerm | int = MemberPerm.Member,
        send_alert: bool = False,
        alert_text: str = '你没有权限执行此指令',
        allow_override: bool = True,
    ) -> Depend:
        """
        群消息权限检查

        指示需要 `level` 以上等级才能触发

        :param perm: 至少需要什么权限才能调用
        :param send_alert: 是否发送无权限警告
        :param alert_text: 无权限提示的消息内容
        :param allow_override: 是否允许bot主人和bot管理员无视权限控制
        """

        async def check_wrapper(app: Ariadne, group: Group, member: Member):
            if group.id in blacklist_cfg.groups or member.id in blacklist_cfg.users:
                raise ExecutionStop()
            level = await cls.get(member, allow_override)
            if isinstance(perm, MemberPerm):
                if level < cls._levels[perm]:
                    if send_alert:
                        await safeSendGroupMessage(group, MessageChain.create(At(member.id), Plain(' ' + alert_text)))
                    raise ExecutionStop()
            elif isinstance(perm, int):
                if level < perm:
                    if send_alert:
                        await safeSendGroupMessage(group, MessageChain.create(At(member.id), Plain(' ' + alert_text)))
                    raise ExecutionStop()

        return Depend(check_wrapper)


class TempPermission(Permission):
    @classmethod
    def require(
        cls,
        perm: MemberPerm | int = MemberPerm.Member,
        send_alert: bool = False,
        alert_text: str = '你没有权限执行此指令',
        allow_override: bool = True,
    ) -> Depend:
        """
        临时消息权限检查

        指示需要 `level` 以上等级才能触发

        :param perm: 至少需要什么权限才能调用
        :param send_alert: 是否发送无权限警告
        :param alert_text: 无权限提示的消息内容
        :param allow_override: 是否允许bot主人和bot管理员无视权限控制
        """

        async def check_wrapper(app: Ariadne, member: Member):
            if member.id in blacklist_cfg.users:
                raise ExecutionStop()
            level = await cls.get(member, allow_override)
            if isinstance(perm, MemberPerm):
                if level < cls._levels[perm]:
                    if send_alert:
                        await app.sendTempMessage(member, MessageChain.create(Plain(alert_text)))
                    raise ExecutionStop()
            elif isinstance(perm, int):
                if level < perm:
                    if send_alert:
                        await app.sendTempMessage(member, MessageChain.create(Plain(alert_text)))
                    raise ExecutionStop()

        return Depend(check_wrapper)


class FriendPermission(Permission):
    @classmethod
    def require(
        cls,
        perm: int = 10,
        send_alert: bool = False,
        alert_text: str = '你没有权限执行此指令',
        allow_override: bool = True,
    ) -> Depend:
        """
        私聊消息权限检查

        指示需要 `level` 以上等级才能触发，仅支持检查是否是bot管理员或主人

        :param perm: 至少需要什么权限才能调用
        :param send_alert: 是否发送无权限警告
        :param alert_text: 无权限提示的消息内容
        :param allow_override: 是否允许bot主人和bot管理员无视权限控制
        """

        async def check_wrapper(app: Ariadne, friend: Friend):
            if friend.id in blacklist_cfg.users:
                raise ExecutionStop()
            level = await cls.get(friend, allow_override)
            if level < perm:
                if send_alert:
                    await app.sendFriendMessage(friend, MessageChain.create(Plain(alert_text)))
                raise ExecutionStop()

        return Depend(check_wrapper)
