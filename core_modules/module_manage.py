#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bot 管理
包含 分群配置 插件配置更改 菜单
"""

import asyncio
import os
from os.path import dirname, split
from pathlib import Path

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Plain
from graia.ariadne.message.parser.twilight import RegexMatch, RegexResult, Twilight
from graia.ariadne.model import Group, Member, MemberPerm
from graia.ariadne.util.interrupt import FunctionWaiter
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger

from util.config import basic_cfg, modules_cfg
from util.control import DisableModule
from util.control.permission import GroupPermission
from util.module_register import Module, Modules
from util.text2img import Text2ImgConfig, async_generate_img, hr

saya = Saya.current()
channel = Channel.current()

module_name = split(dirname(__file__))[-1]

# ensp = ' '  # 半角空格
# emsp = ' '  # 全角空格


Module(
    name='Bot模块管理',
    file_name=module_name,
    author=['Red_lnn'],
    description='管理Bot已加载的模块',
    usage=(
        '[!！.](菜单|menu) —— 获取模块列表\n'
        '[!！.]启用模块 <模块ID> —— 【管理员】启用某个已禁用的模块（全局禁用除外）\n'
        '[!！.]禁用模块 <模块ID> —— 【管理员】禁用某个已启用的模块（禁止禁用的模块除外）\n'
        '[!！.]重载模块 <模块ID> —— 【Bot管理员，强烈不推荐】重载指定模块\n'
        '[!！.]加载模块 <模块文件名> —— 【Bot管理员】加载新模块（文件名无需后缀）\n'
        '[!！.]卸载模块 <模块ID> —— 【Bot管理员，强烈不推荐】卸载指定模块\n'
    ),
    can_disable=False,
).register()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.](菜单|menu)')])],
        decorators=[GroupPermission.require(), DisableModule.require(module_name)],
    )
)
async def menu(app: Ariadne, group: Group):
    msg_send = f'-= {basic_cfg.botName} 功能菜单 for {group.id} =-\n' f'-= {group.name} =-\n{hr}\nID    模块状态    模块名\n'
    for i, module in enumerate(Modules, start=1):
        global_disabled = module.file_name in modules_cfg.globalDisabledModules
        disabled_groups = (
            modules_cfg.disabledGroups[module.file_name] if module.file_name in modules_cfg.disabledGroups else []
        )
        num = f' {i}' if i < 10 else str(i)
        if global_disabled:
            status = '【全局禁用】'
        elif group.id in disabled_groups:
            status = '【本群禁用】'
        elif len(disabled_groups) > 0:
            status = '【本群启用】'
        else:
            status = '【全局启用】'
        msg_send += f'{num}. {status}  {module.name}\n'
    msg_send += (
        f'{hr}\n'
        f'私は {basic_cfg.admin.masterName} の {basic_cfg.botName} です www\n'
        '群管理员要想配置模块开关请发送【.启用/禁用模块 <id>】\n'
        '要想查询某模块的用法和介绍请发送【.用法 <id>】\n'
        '若无法触发，请检查前缀符号是否正确如！与!\n'
        '或是命令中有无多余空格，除了特别说明，其他模块均不需要@bot\n'
        '全局禁用的模块不能重新开启\n'
    )
    img_bytes = await async_generate_img([msg_send], Text2ImgConfig(FontName='sarasa-mono-sc-semibold.ttf'))
    await app.sendMessage(group, MessageChain.create(Image(data_bytes=img_bytes)))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]启用模块')], 'module_id' @ RegexMatch(r'\d+'))],
        decorators=[GroupPermission.require(MemberPerm.Administrator), DisableModule.require(module_name)],
    )
)
async def enable_module(app: Ariadne, group: Group, module_id: RegexResult):
    target_id = int(module_id.result.asDisplay()) - 1  # type: ignore
    if target_id >= len(Modules):
        await app.sendMessage(group, MessageChain.create(Plain('你指定的模块不存在')))
    target_module: Module = Modules[target_id]
    global_disabled: bool = (
        target_module.file_name in modules_cfg.globalDisabledModules
    )

    disabled_groups = (
        modules_cfg.disabledGroups[target_module.file_name]
        if target_module.file_name in modules_cfg.disabledGroups
        else []
    )
    if global_disabled:
        await app.sendMessage(group, MessageChain.create(Plain('模块已全局禁用无法开启')))
    elif group.id in disabled_groups:
        disabled_groups.remove(group.id)
        modules_cfg.disabledGroups[target_module.file_name] = disabled_groups
        modules_cfg.save()
        await app.sendMessage(group, MessageChain.create(Plain('模块已启用')))
    else:
        await app.sendMessage(group, MessageChain.create(Plain('无变化，模块已处于开启状态')))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]禁用模块')], 'module_id' @ RegexMatch(r'\d+'))],
        decorators=[GroupPermission.require(MemberPerm.Administrator), DisableModule.require(module_name)],
    )
)
async def disable_module(app: Ariadne, group: Group, module_id: RegexResult):
    target_id = int(module_id.result.asDisplay()) - 1  # type: ignore
    if target_id >= len(Modules):
        await app.sendMessage(group, MessageChain.create(Plain('你指定的模块不存在')))
    target_module: Module = Modules[target_id]
    disabled_groups = (
        modules_cfg.disabledGroups[target_module.file_name]
        if target_module.file_name in modules_cfg.disabledGroups
        else []
    )
    if not target_module.can_disable:
        await app.sendMessage(group, MessageChain.create(Plain('你指定的模块不允许禁用')))
    elif group.id not in disabled_groups:
        disabled_groups.append(group.id)
        modules_cfg.disabledGroups[target_module.file_name] = disabled_groups
        modules_cfg.save()
        await app.sendMessage(group, MessageChain.create(Plain('模块已禁用')))
    else:
        await app.sendMessage(group, MessageChain.create(Plain('无变化，模块已处于禁用状态')))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]用法')], 'module_id' @ RegexMatch(r'\d+'))],
        decorators=[GroupPermission.require(), DisableModule.require(module_name)],
    )
)
async def get_usage(app: Ariadne, group: Group, module_id: RegexResult):
    target_id = int(module_id.result.asDisplay()) - 1  # type: ignore
    if target_id >= len(Modules):
        await app.sendMessage(group, MessageChain.create(Plain('你指定的模块不存在')))
        return
    target_module: Module = Modules[target_id]
    disabled_groups = (
        modules_cfg.disabledGroups[target_module.file_name]
        if target_module.file_name in modules_cfg.disabledGroups
        else []
    )
    if group.id in disabled_groups:
        await app.sendMessage(group, MessageChain.create(Plain('该模块已在本群禁用')))
        return
    authors = ''
    if target_module.author:
        for author in target_module.author:
            authors += f'{author}, '
        authors = authors.rstrip(', ')
    msg_send = f"{target_module.name}{f' By {authors}' if authors else ''}\n\n"
    if target_module.description:
        msg_send += '>>>>>>>>>>>>>>>>>>>>> 模块描述 <<<<<<<<<<<<<<<<<<<<<\n' + target_module.description + '\n\n'
    if target_module.usage:
        msg_send += '>>>>>>>>>>>>>>>>>>>>> 模块用法 <<<<<<<<<<<<<<<<<<<<<\n' + target_module.usage + '\n\n'
    if target_module.arg_description:
        msg_send += '>>>>>>>>>>>>>>>>>>>>> 参数介绍 <<<<<<<<<<<<<<<<<<<<<\n' + target_module.arg_description
    img_bytes = await async_generate_img([msg_send], Text2ImgConfig(FontName='sarasa-mono-sc-semibold.ttf'))
    await app.sendMessage(group, MessageChain.create(Image(data_bytes=img_bytes)))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]重载模块')], 'module_id' @ RegexMatch(r'\d+'))],
        decorators=[GroupPermission.require(GroupPermission.BOT_ADMIN), DisableModule.require(module_name)],
    )
)
async def reload_module(app: Ariadne, group: Group, member: Member, module_id: RegexResult):
    # 重载即卸载重新加载，在加载含有 `saya = Saya.current()` 的模块时 100% 报错
    await app.sendMessage(
        group,
        MessageChain.create(
            At(member.id), Plain(' 重载模块有极大可能会出错且只有重启bot才能恢复，请问你确实要重载吗？\n强制重载请在10s内发送 .force ，取消请发送 .cancel')
        ),
    )

    async def waiter(waiter_group: Group, waiter_member: Member, waiter_message: MessageChain) -> bool | None:
        if waiter_group.id == group.id and waiter_member.id == member.id:
            saying = waiter_message.asDisplay()
            if saying == '.force':
                return True
            elif saying == '.cancel':
                return False
            else:
                await app.sendMessage(group, MessageChain.create(At(member.id), Plain('请发送 .force 或 .cancel')))

    try:
        answer = await FunctionWaiter(waiter, [GroupMessage]).wait(timeout=10)
    except asyncio.exceptions.TimeoutError:
        await app.sendMessage(group, MessageChain.create(Plain('已超时取消')))
        return
    if not answer:
        await app.sendMessage(group, MessageChain.create(Plain('已取消操作')))
        return

    target_id = int(module_id.result.asDisplay()) - 1  # type: ignore
    if target_id >= len(Modules):
        await app.sendMessage(group, MessageChain.create(Plain('你指定的模块不存在')))
    target_module: Module = Modules[target_id]
    target_filename = target_module.file_name if target_module.file_name[-3:] != '.py' else target_module.file_name[:-3]
    logger.info(f'重载模块: {target_module.name} —— modules.{target_filename}')
    try:
        saya.reload_channel(saya.channels[f'modules.{target_filename}'])
    except Exception as e:
        await app.sendMessage(group, MessageChain.create(Plain(f'重载模块 modules.{target_filename} 时出错')))
        Modules.remove(target_module)
        logger.error(f'重载模块 modules.{target_filename} 时出错')
        logger.exception(e)
    else:
        await app.sendMessage(group, MessageChain.create(Plain(f'重载模块 modules.{target_filename} 成功')))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]加载模块')], 'module_id' @ RegexMatch(r'\d+'))],
        decorators=[GroupPermission.require(GroupPermission.BOT_ADMIN), DisableModule.require(dirname(__file__))],
    )
)
async def load_module(app: Ariadne, group: Group, member: Member, module_id: RegexResult):
    # 在加载含有 `saya = Saya.current()` 的模块时 100% 报错
    await app.sendMessage(
        group, MessageChain.create(At(member.id), Plain(' 加载新模块有极大可能会出错，请问你确实吗？\n强制加载请在10s内发送 .force ，取消请发送 .cancel'))
    )

    async def waiter(waiter_group: Group, waiter_member: Member, waiter_message: MessageChain) -> bool | None:
        if waiter_group.id == group.id and waiter_member.id == member.id:
            saying = waiter_message.asDisplay()
            if saying == '.force':
                return True
            elif saying == '.cancel':
                return False
            else:
                await app.sendMessage(group, MessageChain.create(At(member.id), Plain('请发送 .force 或 .cancel')))

    try:
        answer = await FunctionWaiter(waiter, [GroupMessage]).wait(timeout=600)
    except asyncio.exceptions.TimeoutError:
        await app.sendMessage(group, MessageChain.create(Plain('已超时取消')))
        return
    if not answer:
        await app.sendMessage(group, MessageChain.create(Plain('已取消操作')))
        return
    match_result = module_id.result.asDisplay()  # type: ignore
    target_filename = match_result if match_result[-3:] != '.py' else match_result[:-3]
    modules_dir_list = os.listdir(Path(Path.cwd(), 'modules'))
    if target_filename + '.py' in modules_dir_list or target_filename in modules_dir_list:
        try:
            saya.require('modules.' + target_filename)
        except Exception as e:
            await app.sendMessage(group, MessageChain.create(Plain(f'加载模块 modules.{target_filename} 时出错')))
            logger.error(f'加载模块 modules.{target_filename} 时出错')
            logger.exception(e)
            return
        else:
            await app.sendMessage(group, MessageChain.create(Plain(f'加载模块 modules.{target_filename} 成功')))
            return
    else:
        await app.sendMessage(group, MessageChain.create(Plain(f'模块 modules.{target_filename} 不存在')))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]卸载模块')], 'module_id' @ RegexMatch(r'\d+'))],
        decorators=[GroupPermission.require(GroupPermission.BOT_ADMIN), DisableModule.require(module_name)],
    )
)
async def unload_module(app: Ariadne, group: Group, module_id: RegexResult):
    target_id = int(module_id.result.asDisplay()) - 1  # type: ignore
    if target_id >= len(Modules):
        await app.sendMessage(group, MessageChain.create(Plain('你指定的模块不存在')))
    target_module: Module = Modules[target_id]
    if not target_module.can_disable:
        await app.sendMessage(group, MessageChain.create(Plain('你指定的模块不允许禁用或卸载')))
        return
    target_filename = target_module.file_name if target_module.file_name[-3:] != '.py' else target_module.file_name[:-3]
    logger.debug(f'原channels: {saya.channels}')
    logger.debug(f'要卸载的channel: {saya.channels["modules.BiliVideoInfo"]}')
    logger.info(f'卸载模块: {target_module.name} —— modules.{target_filename}')
    try:
        saya.uninstall_channel(saya.channels[f'modules.{target_filename}'])
    except Exception as e:
        await app.sendMessage(group, MessageChain.create(Plain(f'卸载模块 modules.{target_filename} 时出错')))
        Modules.remove(target_module)
        logger.error(f'卸载模块 modules.{target_filename} 时出错')
        logger.exception(e)
    else:
        logger.debug(f'卸载后的channels: {saya.channels}')
        await app.sendMessage(group, MessageChain.create(Plain(f'卸载模块 modules.{target_filename} 成功')))
        Modules.remove(target_module)
