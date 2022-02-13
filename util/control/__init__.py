#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graia.ariadne.model import Group
from graia.broadcast import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from util.config import modules_cfg


class DisableModule:
    """
    用于管理模块的类，不应该被实例化
    """

    @classmethod
    def require(cls, module_name: str) -> Depend:
        def wrapper(group: Group):
            if module_name in modules_cfg.globalDisabledModules:
                raise ExecutionStop()
            elif module_name in modules_cfg.disabledGroups:
                if group.id in modules_cfg.disabledGroups[module_name]:
                    raise ExecutionStop()

        return Depend(wrapper)
