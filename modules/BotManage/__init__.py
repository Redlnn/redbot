#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bot 管理
包含 分群配置 插件配置更改 菜单
"""

from asyncio import Lock
from typing import List, Optional

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.message.parser.pattern import RegexMatch
from graia.ariadne.message.parser.twilight import Sparkle, Twilight
from graia.ariadne.model import Group, MemberPerm
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema

from config import config_data, reload_config, save_config
from utils.Limit.Permission import Permission
from utils.Limit.Rate import GroupInterval
from utils.TextWithImg2Img import reload_config as gen_img_reload
from .TextWithImg2Img import async_generate_img, hr

lock: Lock = Lock()
saya = Saya.current()
channel = Channel.current()

ensp = ' '  # 半角空格
emsp = ' '  # 全角空格

Modules: List = []


class Module:
    name: str  # 模块名称
    config_name: str  # 模块在配置文件中的名称
    author: List[str] = None  # 作者列表
    description: Optional[str] = None  # 模块描述
    usage: Optional[str] = None  # 模块用法
    arg_description: Optional[str] = None  # 参数描述
    can_disable: bool = True  # 可否分群关闭

    def __init__(
            self,
            name: str,  # 模块名称
            config_name: str,  # 模块在配置文件中的名称
            author: List[str] = None,  # 作者列表
            description: Optional[str] = None,  # 模块描述
            usage: Optional[str] = None,  # 模块用法
            arg_description: Optional[str] = None,  # 参数描述
            can_disable: bool = True,  # 可否分群关闭
    ):
        self.name = name
        self.config_name = config_name
        self.author = author
        self.description = description
        self.usage = usage
        self.arg_description = arg_description
        self.can_disable = can_disable

    def registe(self):
        Modules.append(self)


Module(
        name='Bot模块管理',
        config_name='BotManage',
        author=['Red_lnn'],
        description='管理Bot已加载的模块',
        usage=(
            '[!！.](菜单|menu) —— 获取模块列表\n'
            '[!！.]启用模块 <模块ID> —— 【管理员】启用某个已禁用的模块（全局禁用除外）\n'
            '[!！.]禁用模块 <模块ID> —— 【管理员】禁用某个已启用的模块（禁止禁用的模块除外）\n'
            '[!！.]reload —— 【Bot管理员】重载Bot和模块的配置文件（不影响部分模块）'
        ),
        can_disable=False
).registe()


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.](菜单|menu)')]))],
                decorators=[GroupInterval.require(5)],
        )
)
async def menu(app: Ariadne, group: Group):
    msg_send = (
        f'-= {config_data["Basic"]["BotName"]} 菜单 for {group.id} =-\n' f'{group.name}\n' f'{hr}\n' 'ID    模块状态    模块名\n'
    )
    i = 0
    for module in Modules:
        i += 1
        global_disabled = not config_data['Modules'][module.config_name]['Enabled']
        disabled_groups = config_data['Modules'][module.config_name]['DisabledGroup']
        num = f' {i}' if i < 10 else str(i)
        if global_disabled:
            status = f'【全局禁用】'
        elif group.id in disabled_groups:
            status = f'【本群禁用】'
        else:
            status = f'            '
        msg_send += f'{num}. {status}  {module.name}\n'
    msg_send += (
        f'{hr}\n'
        '群管理员要想配置模块开关请发送【.启用/禁用模块 <id>】\n'
        '要想查询某模块的用法请发送【.用法 <id>】\n'
        '若无法触发，请检查前缀符号是否正确如 ! 与 ！\n'
        '或是命令中有无多余空格，所有模块均不需要@bot\n'
        '全局禁用的模块不能重新开启'
    )
    img_io = await async_generate_img([msg_send])
    await app.sendGroupMessage(group, MessageChain.create(Image(data_bytes=img_io.getvalue())))


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]启用模块\ '), RegexMatch(r'\d+')]))],
                decorators=[GroupInterval.require(5), Permission.group_perm_check(MemberPerm.Administrator)],
        )
)
async def turn_on(app: Ariadne, group: Group, sparkle: Sparkle):
    targe_id = int(sparkle._check_1.result.asDisplay())
    target_module = Modules[targe_id - 1]
    global_disabled = not config_data['Modules'][target_module.config_name]['Enabled']
    disabled_groups = config_data['Modules'][target_module.config_name]['DisabledGroup']
    if global_disabled:
        await app.sendGroupMessage(group, MessageChain.create(Plain('模块已全局禁用无法开启')))
    elif group.id in disabled_groups:
        disabled_groups.remove(group.id)
        config_data['Modules'][target_module.config_name]['DisabledGroup'] = disabled_groups
        save_config()
        await app.sendGroupMessage(group, MessageChain.create(Plain('模块已启用')))
    else:
        await app.sendGroupMessage(group, MessageChain.create(Plain('无变化，模块已处于开启状态')))


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]禁用模块\ '), RegexMatch(r'\d+')]))],
                decorators=[GroupInterval.require(5), Permission.group_perm_check(MemberPerm.Administrator)],
        )
)
async def turn_off(app: Ariadne, group: Group, sparkle: Sparkle):
    targe_id = int(sparkle._check_1.result.asDisplay())
    target_module = Modules[targe_id - 1]
    disabled_groups = config_data['Modules'][target_module.config_name]['DisabledGroup']
    if not target_module.can_disable:
        await app.sendGroupMessage(group, MessageChain.create(Plain('模块已设置禁止禁用')))
    elif group.id not in disabled_groups:
        disabled_groups.append(group.id)
        config_data['Modules'][target_module.config_name]['DisabledGroup'] = disabled_groups
        save_config()
        await app.sendGroupMessage(group, MessageChain.create(Plain('模块已禁用')))
    else:
        await app.sendGroupMessage(group, MessageChain.create(Plain('无变化，模块已处于禁用状态')))


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]reload')]))],
                decorators=[GroupInterval.require(5), Permission.group_perm_check(Permission.BOT_ADMIN)],
        )
)
async def turn_off(app: Ariadne, group: Group):
    async with lock:
        await app.sendGroupMessage(group, MessageChain.create(Plain('重新加载配置文件')))
        if reload_config():
            try:
                gen_img_reload()
            except Exception as e:
                await app.sendGroupMessage(group, MessageChain.create(Plain(f'重新加载文本图像转图片的配置文件时出错，错误内容：{e}')))
            return
        else:
            await app.sendGroupMessage(group, MessageChain.create(Plain('加载配置文件时出错，请联系bot管理员')))
