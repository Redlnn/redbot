#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graia.ariadne.event.message import GroupMessage
from graia.broadcast import ExecutionStop
from graia.broadcast.builtin.decorators import Depend
from graia.broadcast.entities.event import Dispatchable

from util.config import modules_cfg


class DisableModule:
    """
    用于管理模块的类，不应该被实例化
    """

    @classmethod
    def require(cls, module_name: str) -> Depend:
        def wrapper(event: Dispatchable):
            if module_name in modules_cfg.globalDisabledModules:
                raise ExecutionStop()
            elif isinstance(event, GroupMessage) and module_name in modules_cfg.disabledGroups:
                if event.sender.group.id in modules_cfg.disabledGroups[module_name]:
                    raise ExecutionStop()

        return Depend(wrapper)
