"""
用法：

在本Bot账号所在的任一一QQ群中发送 `!roll` 或 `!roll {任意字符}` 均可触发本插件功能
触发后会回复一个由0至100之间的任一随机整数
"""

from random import randint

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Dice, Plain, Source
from graia.ariadne.message.parser.twilight import (
    RegexMatch,
    RegexResult,
    Twilight,
    WildcardMatch,
)
from graia.ariadne.model import Group
from graia.ariadne.util.saya import decorate, dispatch, listen
from graia.saya import Channel

from util.control import require_disable
from util.control.permission import GroupPermission

channel = Channel.current()

channel.meta['name'] = '随机数'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = '获得一个随机数\n用法：\n  [!！.]roll {要roll的事件}\n  [!！.](dice|骰子|色子)'


@listen(GroupMessage)
@dispatch(Twilight(RegexMatch(r'[!！.]roll'), 'target' @ WildcardMatch()))
@decorate(GroupPermission.require(), require_disable(channel.module))
async def roll(app: Ariadne, group: Group, source: Source, target: RegexResult):
    if target.result is None:
        return
    t = str(target.result).strip()
    chain = MessageChain(Plain(f'{t}的概率为：{randint(0, 100)}')) if t else MessageChain(Plain(str(randint(0, 100))))
    await app.send_message(group, chain, quote=source)


@listen(GroupMessage)
@dispatch(Twilight(RegexMatch(r'[!！.](dice|骰子|色子)')))
@decorate(GroupPermission.require(), require_disable(channel.module))
async def dice(app: Ariadne, group: Group):
    await app.send_message(group, MessageChain(Dice(randint(1, 6))))
