from graia.ariadne.event.message import GroupMessage, MessageEvent
from graia.ariadne.event.mirai import NudgeEvent
from graia.broadcast import ExecutionStop
from graia.broadcast.builtin.decorators import Depend
from graia.broadcast.entities.event import Dispatchable

from libs.config import modules_cfg


def require_disable(module_name: str) -> Depend:
    def wrapper(event: Dispatchable):
        if module_name in modules_cfg.globalDisabledModules:
            raise ExecutionStop
        elif module_name in modules_cfg.disabledGroups:
            if isinstance(event, MessageEvent):
                if isinstance(event, GroupMessage) and event.sender.group.id in modules_cfg.disabledGroups[module_name]:
                    raise ExecutionStop
                elif event.sender.id in modules_cfg.disabledGroups[module_name]:
                    raise ExecutionStop
            elif isinstance(event, NudgeEvent) and event.target in modules_cfg.disabledGroups[module_name]:
                raise ExecutionStop
            elif hasattr(event, 'group') and getattr(event, 'group') in modules_cfg.disabledGroups[module_name]:
                raise ExecutionStop

    return Depend(wrapper)
