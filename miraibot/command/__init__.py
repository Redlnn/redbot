from typing import Dict, Union, Tuple, List

from graia.application.entry import GraiaMiraiApplication, MessageChain, Group, Member, Friend, At, Plain, MemberPerm

from miraibot import GetCore
from .ExecClass import ExecClass

group_commands: Dict[str, ExecClass] = {}
friend_commands: Dict = {}
bcc = GetCore.bcc()


class CommandDecorators(Exception):
    pass


def group_command(
        command: str,
        aliases: Union[Tuple[str], List[str]] = (),
        group: Union[Tuple[int], List[int]] = [],  # 当 group 保持为空时，可针对所有群启用 # noqa
        permission: List[MemberPerm] = [  # noqa
            MemberPerm.Member, MemberPerm.Administrator, MemberPerm.Owner
        ],  # 命令权限
        at: bool = False,  # 是否被 at
        shell_like: bool = False  # 是否使用类 shell 语法
):
    """命令处理器
        将一个命令处理器装入指令池中

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
    if message.has(At):
        m = message.get(Plain)[0].text.strip()
    else:
        m = message.asDisplay().rstrip()
    command = f"{m}_{group.id}"
    if command not in group_commands:
        return
    elif f"{m}_null" in group_commands:
        command = f"{m}_null"
        target = group_commands[command]
        if member.permission not in target.Permission:  # 检查指令需求的权限
            await bot.sendGroupMessage(group, MessageChain.create([
                Plain('你没有权限执行此命令')
            ]))
            return
        if target.At:
            for i in message.get(At):
                if i.target == bot.connect_info.account:
                    await group_commands[command].Target(
                        **group_commands[command].Target.__annotations__
                    )
        else:
            await group_commands[command].Target(
                **group_commands[command].Target.__annotations__
            )
        del target
    else:
        if group_commands[command].Group:
            if group.id == group_commands[command].Group:  # 检查指令是否适用当前群
                target = group_commands[command]
                if member.permission not in target.Permission:  # 检查指令需求的权限
                    await bot.sendGroupMessage(group, MessageChain.create([
                        Plain('你没有权限执行此命令')
                    ]))
                    return
                if target.At:
                    for i in message.get(At):
                        if i.target == bot.connect_info.account:
                            await group_commands[command].Target(
                                **group_commands[command].Target.__annotations__
                            )
                else:
                    await group_commands[command].Target(
                        **group_commands[command].Target.__annotations__
                    )
                del target
    del m, command


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
