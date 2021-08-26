"""
群指令系统示例插件
示例用法:
@bot test
@bot t
@bot tt
"""
from graia.application.entry import (GraiaMiraiApplication, Member, MemberPerm, Group, MessageChain, GroupMessage)

from miraibot import GetCore
from miraibot.command import group_command

bcc = GetCore.bcc()
__plugin_name__ = "群指令系统示例插件"
__plugin_usage__ = "群指令系统测试，可用命令：test、t、tt，需要的权限为管理员或群组，需要机器人被At"


@group_command(
    command='test',
    aliases=['t', 'tt'],
    group=[123456789],
    permission=[MemberPerm.Administrator, MemberPerm.Owner],
    at=True
)
async def group_command_listener(
        app: GraiaMiraiApplication,
        group: Group,
        message: MessageChain,
        member: Member,
        event: GroupMessage
):
    print(app, group, message, member, event, sep='\n')
