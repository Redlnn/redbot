from typing import Dict, Union, Tuple, List
from ..event import MemberPerm
from .ExecClass import ExecClass

from .. import GraiaMiraiApplication, get
from ..message import MessageChain, Group, Member, Friend, At


group_commands: Dict[ExecClass] = {}
friend_commands: Dict = {}
bcc = get.bcc()


class CommandDecorators(Exception):
    pass


def group_command(
    command: str,
    aliases: Tuple[str] = (),
    group: Union[Tuple[int], List[int]] = [],  # noqa
    permission: List[MemberPerm] = [  # noqa
        MemberPerm.Member, MemberPerm.Administrator, MemberPerm.Owner
    ],  # 命令权限
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
    :return: None
    """
    def command_decorator(func):
        def append(group):
            my_command = f"{command}_{group}" if command not in [
                k for k, v in group_commands.items()
            ] else None

            if my_command is not None:
                # global group_commands
                group_commands[my_command] = ExecClass(
                    name=my_command,
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
                raise CommandDecorators(f"命令 \"{command}\" 已被占用")
        if len(group):
            for group_id in group:
                append(group_id)
        else:
            append("null")
        return func
    return command_decorator


@bcc.receiver("GroupMessage")
async def Group_instruction_processor(
    bot: GraiaMiraiApplication,
    message: MessageChain,
    group: Group, member: Member
):
    async with message.asDisplay() as m:
        if m in group_commands:
            if group_commands[m].Group:
                if group.id in group_commands[m].Group:  # 检查指令是否适用当前群
                    async with group_commands[m] as target:
                        if member.permission not in target.Permission:  # 检查指令需求的权限 # noqa
                            return
                        if target.at:
                            for i in message.get(At):
                                if i.target == bot.connect_info.account:
                                    await group_commands[m].Target(
                                        **group_commands[m].Target.__annotations__() # noqa
                                    )

    for k, v in group_commands.items():
        if message.asDisplay() == k:
            await v()


@bcc.receiver("FriendMessage")
async def f_instruction_processor(
    bot: GraiaMiraiApplication,
    message: MessageChain,
    friend: Friend, member: Member
):
    for k, v in friend_commands.items():
        if message.asDisplay() == k:
            await v()


__all__ = ["group_command"]
