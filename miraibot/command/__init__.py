from typing import Dict, Union, Tuple, List
from ..event import MemberPerm
from .ExecClass import ExecClass

group_commands: Dict = {}
friend_commands: Dict = {}


class command_decorators(Exception):
    pass


def group_command(
    command: str,  # 命令名
    aliases=(),  # 命令别名
    group=[],
    permission=MemberPerm.Member,  # 命令权限
    at=False,  # 是否被 at
    shell_like=False  # 是否使用类 shell 语法
):

    """命令处理器
        将一个命令处理器装入指令池中

    :param category: 群或好友，可选参数仅有 Group 或 Friend
    :param command: 命令名
    :param aliases: 命令别名, 单个可用字符串，多个请传入元组
    :param group: 命令适用的群, 可以是 list 或 tuple 但内部必须是 int
    :param permission: 命令权限
    :param at: 机器人是否被 at
    :param shell_like: 是否使用类 shell 语法
    :param reutrn: None
    """
    def command_decorator(func):
        my_command = command if command not in [
            k for k, v in group_commands.items()
        ] else None

        if not my_command:
            global group_commands
            group_commands[my_command] = ExecClass(
                target=func,
                group=group,
                permission=permission,
                at=at,
                shell_like=shell_like
            )
            if len(aliases):
                for i in aliases:
                    group_commands[i] = ExecClass(
                        target=func,
                        group=group,
                        permission=permission,
                        at=at,
                        shell_like=shell_like
                    )
        else:
            raise command_decorators(f"命令 \"{command}\" 已被占用")

        return func
    return command_decorator
