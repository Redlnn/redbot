from typing import Dict, Union, Tuple, List

from graia.application.entry import GraiaMiraiApplication, MessageChain, Group, Member, Friend, At, Plain, MemberPerm, GroupMessage

from miraibot import GetCore
from .ExecClass import ExecClass

__all__ = ["group_command"]

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
        shell_like: bool = True  # 是否使用类 shell 语法
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


async def group_instruction_processor(
        m: str, command: str,
        bot: GraiaMiraiApplication,
        message: MessageChain,
        group: Group, member: Member,
        event: GroupMessage
):
    target_func = group_commands[command]
    if member.permission not in target_func.Permission:  # 检查指令需求的权限
        await bot.sendGroupMessage(group, MessageChain.create([
            Plain('你没有权限执行此命令')
        ]))
        return

    parm = {
        GraiaMiraiApplication: bot,
        MessageChain: message,
        Member: member,
        Group: group,
        GroupMessage: event
    }

    target_keyword_parm = {}
    for parm_key, parm_type in target_func.Target.__annotations__.items():
        target_keyword_parm.update({parm_key: parm[parm_type]})

    if target_func.Shell_like:
        if target_func.At:
            for i in message.get(At):
                if i.target == bot.connect_info.account:
                    await target_func.Target(**target_keyword_parm)
        elif m == message.asDisplay().strip().split()[0]:
            await target_func.Target(**target_keyword_parm)
    else:
        if target_func.At:
            if message.has(At) and m == message.get(Plain)[0].text.strip():
                await target_func.Target(**target_keyword_parm)
        elif m == message.asDisplay().strip():
            await target_func.Target(**target_keyword_parm)

    del target_func, target_keyword_parm


@bcc.receiver("GroupMessage")
async def group_instruction_pre_processor(
        bot: GraiaMiraiApplication,
        message: MessageChain,
        group: Group, member: Member,
        event: GroupMessage
):
    if message.has(At):
        m = message.get(Plain)[0].text.strip().split()[0]
    else:
        m = message.asDisplay().strip().split()[0]

    command = f"{m}_{group.id}"
    if f"{m}_null" in group_commands:
        await group_instruction_processor(m, f"{m}_null", bot, message, group, member, event)
    elif command not in group_commands:
        return
    elif group_commands[command].Group and group.id == group_commands[command].Group:  # 检查指令是否适用当前群
        await group_instruction_processor(m, command, bot, message, group, member, event)
    del m, command


@bcc.receiver("FriendMessage")
async def friend_instruction_processor(
        bot: GraiaMiraiApplication,
        message: MessageChain,
        friend: Friend, member: Member
):
    for k, v in friend_commands.items():
        if message.asDisplay() == k:
            await v()
