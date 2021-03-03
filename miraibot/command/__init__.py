from typing import Dict, Union, Tuple, List
from ..event import MemberPerm
from .ExecClass import ExecClass

group_commands: Dict = {}
friend_commands: Dict = {}


class command_decorators(Exception):
    pass


def group_command(
    command: str,
    aliases: Tuple = (),
    group: Union[Tuple, List] = [],
    permission: Union[
        MemberPerm.Administrator, MemberPerm.Owner, MemberPerm.Member
    ] = MemberPerm.Member,  # 命令权限
    at: bool = False,  # 是否被 at
    shell_like: bool = False  # 是否使用类 shell 语法
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
        def append(group):
            my_command = f"{command}_{group}" if command not in [
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
                        group_commands[
                            f"{i}_{group}"
                        ] = group_commands[my_command]
            else:
                raise command_decorators(f"命令 \"{command}\" 已被占用")
        if len(group):
            for group_id in group:
                append(group_id)
        else:
            append("null")
        return func
    return command_decorator
