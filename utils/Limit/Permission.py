#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
权限检查

Xenon 管理：https://github.com/McZoo/Xenon/blob/master/lib/control.py
"""

from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain
from graia.ariadne.model import Group, Member, MemberPerm
from graia.broadcast import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from config import config_data

__all__ = ['Permission']


class Permission:
    """
    用于管理权限的类，不应被实例化

    适用于群消息和来自群的临时会话
    """

    MASTER: int = 100
    BOT_ADMIN: int = 90
    OWMER: int = 30
    ADMIN: int = 20
    USER: int = 10
    BANED: int = 0
    DEFAULT: int = USER

    _levels = {
        MemberPerm.Member: USER,
        MemberPerm.Administrator: ADMIN,
        MemberPerm.Owner: OWMER,
    }

    @classmethod
    async def get(cls, member: Member, allow_override: bool = True) -> int:
        """
        获取用户的权限等级

        :param member: 群成员实例
        :param allow_override: 是否允许bot主任无视权限控制
        :return: 等级，整数
        """
        if allow_override:
            admins = config_data['Basic']['Permission']['Admin'] if config_data['Basic']['Permission']['Admin'] else []
            if member.id == config_data['Basic']['Permission']['Master']:
                return cls.MASTER
            elif member.id in admins:
                return cls.BOT_ADMIN

        match member.permission:
            case MemberPerm.Owner:
                return cls.OWMER
            case MemberPerm.Administrator:
                return cls.ADMIN
            case MemberPerm.Member:
                return cls.USER
            case _:
                return cls.DEFAULT

    @classmethod
    def group_perm_check(
        cls,
        perm: MemberPerm | int,
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
            level = await cls.get(member, allow_override)
            if isinstance(perm, MemberPerm):
                if level < cls._levels[perm]:
                    if send_alert:
                        await app.sendGroupMessage(group, MessageChain.create(At(member.id), Plain(' ' + alert_text)))
                    raise ExecutionStop()
            elif isinstance(perm, int):
                if level < perm:
                    if send_alert:
                        await app.sendGroupMessage(group, MessageChain.create(At(member.id), Plain(' ' + alert_text)))
                    raise ExecutionStop()

        return Depend(check_wrapper)

    @classmethod
    def temp_perm_check(
        cls,
        perm: MemberPerm | int,
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

        async def check_wrapper(app: Ariadne, member: Member):
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
