#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bot 管理
包含 分群配置 插件配置更改 菜单
"""

import asyncio
import os
from pathlib import Path

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
from util.control import require_disable
from util.control.permission import GroupPermission
from util.text2img import Text2ImgConfig, async_generate_img, hr

saya = Saya.current()
channel = Channel.current()

channel.meta['name'] = 'Bot模块管理'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = '管理Bot已加载的模块\n'
'[!！.](菜单|menu) —— 获取模块列表\n'
'[!！.]启用 <模块ID> —— 【群管理员】启用某个已禁用的模块（全局禁用除外）\n'
'[!！.]禁用 <模块ID> —— 【群管理员】禁用某个已启用的模块（禁止禁用的模块除外）\n'
'[!！.]全局启用 <模块ID> —— 【Bot管理员】全局启用某个已禁用的模块\n'
'[!！.]全局禁用 <模块ID> —— 【Bot管理员】全局禁用某个已启用的模块（禁止禁用的模块除外）\n'
'[!！.]重载 <模块ID> —— 【Bot管理员，强烈不推荐】重载指定模块\n'
'[!！.]加载 <模块文件名> —— 【Bot管理员，强烈不推荐】加载新模块（xxx.xxx 无需后缀）\n'
'[!！.]卸载 <模块ID> —— 【Bot管理员】卸载指定模块'
channel.meta['can_disable'] = False

# ensp = ' '  # 半角空格
# emsp = ' '  # 全角空格


async def get_channel(module_id: str, group: Group):
    if module_id.isdigit():
        target_id = int(module_id) - 1
        if target_id >= len(saya.channels):
            await group.send_message(MessageChain(Plain('你指定的模块不存在')))
            return
        return saya.channels[str(list(saya.channels.keys())[target_id])]
    else:
        if module_id not in saya.channels:
            await group.send_message(MessageChain(Plain('你指定的模块不存在')))
            return
        return saya.channels[module_id]


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.](菜单|menu)')])],
        decorators=[GroupPermission.require(), require_disable(channel.module)],
    )
)
async def menu(group: Group):
    msg_send = f'-= {basic_cfg.botName} 功能菜单 for {group.id} =-\n-= {group.name} =-\n{hr}\nID    模块状态    模块名\n'
    for index, module in enumerate(saya.channels, start=1):
        global_disabled = module in modules_cfg.globalDisabledModules
        disabled_groups = modules_cfg.disabledGroups[module] if module in modules_cfg.disabledGroups else []
        num = f' {index}' if index < 10 else str(index)
        if global_disabled:
            status = '【全局禁用】'
        elif group.id in disabled_groups:
            status = '  【禁用】  '
        # if len(disabled_groups) > 0 只有本群启用 else 全局启用
        else:
            status = '            '
        msg_send += f'{num}. {status}  {saya.channels[module]._name if saya.channels[module]._name is not None else saya.channels[module].module}\n'
    msg_send += (
        f'{hr}\n'
        f'私は {basic_cfg.admin.masterName} の {basic_cfg.botName} です www\n'
        '群管理员要想配置模块开关请发送【.启用/禁用 <id>】\n'
        '要想查询某模块的用法和介绍请发送【.用法 <id>】\n'
        '若无法触发，请检查前缀符号是否正确如！与!\n'
        '或是命令中有无多余空格，除特别说明外均不需要 @bot'
    )
    img_bytes = await async_generate_img([msg_send], Text2ImgConfig(FontName='sarasa-mono-sc-semibold.ttf'))
    await group.send_message(MessageChain(Image(data_bytes=img_bytes)))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]启用')], 'module_id' @ RegexMatch(r'\d+'))],
        decorators=[GroupPermission.require(MemberPerm.Administrator), require_disable(channel.module)],
    )
)
async def enable_module(group: Group, module_id: RegexResult):
    if module_id.result is None:
        return
    target_id = module_id.result.display
    target_module = await get_channel(target_id, group)
    if target_module is None:
        await group.send_message(MessageChain(Plain('你指定的模块不存在')))
        return
    disabled_groups = (
        modules_cfg.disabledGroups[target_module.module] if target_module.module in modules_cfg.disabledGroups else []
    )
    if target_module.module in modules_cfg.globalDisabledModules:
        await group.send_message(MessageChain(Plain('模块已全局禁用无法开启')))
    elif group.id in disabled_groups:
        disabled_groups.remove(group.id)
        modules_cfg.disabledGroups[target_module.module] = disabled_groups
        modules_cfg.save()
        await group.send_message(MessageChain(Plain('模块已启用')))
    else:
        await group.send_message(MessageChain(Plain('无变化，模块已处于开启状态')))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]禁用')], 'module_id' @ RegexMatch(r'\d+'))],
        decorators=[GroupPermission.require(MemberPerm.Administrator), require_disable(channel.module)],
    )
)
async def disable_module(group: Group, module_id: RegexResult):
    if module_id.result is None:
        return
    target_module = await get_channel(module_id.result.display, group)
    if target_module is None:
        await group.send_message(MessageChain(Plain('你指定的模块不存在')))
        return
    disabled_groups = (
        modules_cfg.disabledGroups[target_module.module] if target_module.module in modules_cfg.disabledGroups else []
    )
    if not target_module.meta.get('can_disable', True):
        await group.send_message(MessageChain(Plain('你指定的模块不允许禁用')))
    elif group.id not in disabled_groups:
        disabled_groups.append(group.id)
        modules_cfg.disabledGroups[target_module.module] = disabled_groups
        modules_cfg.save()
        await group.send_message(MessageChain(Plain('模块已禁用')))
    else:
        await group.send_message(MessageChain(Plain('无变化，模块已处于禁用状态')))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]全局启用')], 'module_id' @ RegexMatch(r'\d+'))],
        decorators=[GroupPermission.require(MemberPerm.Administrator), require_disable(channel.module)],
    )
)
async def global_enable_module(group: Group, module_id: RegexResult):
    if module_id.result is None:
        return
    target_module = await get_channel(module_id.result.display, group)
    if target_module is None:
        await group.send_message(MessageChain(Plain('你指定的模块不存在')))
        return
    if target_module.module not in modules_cfg.globalDisabledModules:
        await group.send_message(MessageChain(Plain('无变化，模块已处于全局开启状态')))
    else:
        modules_cfg.globalDisabledModules.remove(target_module.module)
        modules_cfg.save()
        await group.send_message(MessageChain(Plain('模块已全局启用')))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]全局禁用')], 'module_id' @ RegexMatch(r'\d+'))],
        decorators=[GroupPermission.require(MemberPerm.Administrator), require_disable(channel.module)],
    )
)
async def global_disable_module(group: Group, module_id: RegexResult):
    if module_id.result is None:
        return
    target_module = await get_channel(module_id.result.display, group)
    if target_module is None:
        await group.send_message(MessageChain(Plain('你指定的模块不存在')))
        return
    if not target_module.meta.get('can_disable', True):
        await group.send_message(MessageChain(Plain('你指定的模块不允许禁用')))
    elif target_module.module not in modules_cfg.globalDisabledModules:
        modules_cfg.globalDisabledModules.append(target_module.module)
        modules_cfg.save()
        await group.send_message(MessageChain(Plain('模块已全局禁用')))
    else:
        await group.send_message(MessageChain(Plain('无变化，模块已处于全局禁用状态')))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]用法')], 'module_id' @ RegexMatch(r'\d+'))],
        decorators=[GroupPermission.require(), require_disable(channel.module)],
    )
)
async def get_usage(group: Group, module_id: RegexResult):
    if module_id.result is None:
        return
    target_module = await get_channel(module_id.result.display, group)
    if target_module is None:
        return
    disabled_groups = (
        modules_cfg.disabledGroups[target_module.module] if target_module.module in modules_cfg.disabledGroups else []
    )
    if group.id in disabled_groups:
        await group.send_message(MessageChain(Plain('该模块已在本群禁用')))
        return
    authors = ''
    if target_module.meta['author']:
        for author in target_module.meta['author']:
            authors += f'{author}, '
        authors = authors.rstrip(', ')
    msg_send = f'{target_module.name}{f" By {authors}" if authors else ""}\n\n'
    if target_module.meta['description']:
        msg_send += '>>>>>>>>>>>>>>>>>>>>>>> 描述 <<<<<<<<<<<<<<<<<<<<<<<\n' + target_module.meta['description'] + '\n\n'
    img_bytes = await async_generate_img([msg_send], Text2ImgConfig(FontName='sarasa-mono-sc-semibold.ttf'))
    await group.send_message(MessageChain(Image(data_bytes=img_bytes)))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]重载模块')], 'module_id' @ RegexMatch(r'\d+'))],
        decorators=[GroupPermission.require(GroupPermission.BOT_ADMIN), require_disable(channel.module)],
    )
)
async def reload_module(group: Group, member: Member, module_id: RegexResult):
    # 重载即卸载重新加载，在加载含有 `saya = Saya.current()` 的模块时 100% 报错
    await group.send_message(
        MessageChain(At(member.id), Plain(' 重载模块有极大可能会出错且只有重启bot才能恢复，请问你确实要重载吗？\n强制重载请在10s内发送 .force ，取消请发送 .cancel')),
    )

    async def waiter(waiter_group: Group, waiter_member: Member, waiter_message: MessageChain) -> bool | None:
        if waiter_group.id == group.id and waiter_member.id == member.id:
            saying = waiter_message.display
            if saying == '.force':
                return True
            elif saying == '.cancel':
                return False
            else:
                await group.send_message(MessageChain(At(member.id), Plain('请发送 .force 或 .cancel')))

    try:
        answer: bool = await FunctionWaiter(waiter, [GroupMessage]).wait(timeout=10)
    except asyncio.exceptions.TimeoutError:
        await group.send_message(MessageChain(Plain('已超时取消')))
        return
    if not answer:
        await group.send_message(MessageChain(Plain('已取消操作')))
        return

    if module_id.result is None:
        return
    target_module = await get_channel(module_id.result.display, group)
    if target_module is None:
        return
    logger.info(f'重载模块: {target_module.name} —— {target_module.module}')
    try:
        saya.reload_channel(saya.channels[target_module.module])
    except Exception as e:
        await group.send_message(MessageChain(Plain(f'重载模块 {target_module.module} 时出错')))
        logger.error(f'重载模块 {target_module.module} 时出错')
        logger.exception(e)
    else:
        await group.send_message(MessageChain(Plain(f'重载模块 {target_module.module} 成功')))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]加载')], 'module_id' @ RegexMatch(r'\d+'))],
        decorators=[GroupPermission.require(GroupPermission.BOT_ADMIN), require_disable(channel.module)],
    )
)
async def load_module(group: Group, member: Member, module_id: RegexResult):
    if module_id.result is None:
        return
    # 在加载含有 `saya = Saya.current()` 的模块时 100% 报错
    await group.send_message(
        MessageChain(At(member.id), Plain(' 加载新模块有极大可能会出错，请问你确实吗？\n强制加载请在10s内发送 .force ，取消请发送 .cancel'))
    )

    async def waiter(waiter_group: Group, waiter_member: Member, waiter_message: MessageChain) -> bool | None:
        if waiter_group.id == group.id and waiter_member.id == member.id:
            saying = waiter_message.display
            if saying == '.force':
                return True
            elif saying == '.cancel':
                return False
            else:
                await group.send_message(MessageChain(At(member.id), Plain('请发送 .force 或 .cancel')))

    try:
        answer: bool = await FunctionWaiter(waiter, [GroupMessage]).wait(timeout=600)
    except asyncio.exceptions.TimeoutError:
        await group.send_message(MessageChain(Plain('已超时取消')))
        return
    if not answer:
        await group.send_message(MessageChain(Plain('已取消操作')))
        return
    match_result = module_id.result.display
    target_filename = match_result if match_result[-3:] != '.py' else match_result[:-3]
    modules_dir_list = os.listdir(Path(Path.cwd(), 'modules'))
    if target_filename + '.py' in modules_dir_list or target_filename in modules_dir_list:
        try:
            saya.require('modules.' + target_filename)
        except Exception as e:
            await group.send_message(MessageChain(Plain(f'加载模块 modules.{target_filename} 时出错')))
            logger.error(f'加载模块 modules.{target_filename} 时出错')
            logger.exception(e)
            return
        else:
            await group.send_message(MessageChain(Plain(f'加载模块 modules.{target_filename} 成功')))
            return
    else:
        await group.send_message(MessageChain(Plain(f'模块 modules.{target_filename} 不存在')))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r'[!！.]卸载')], 'module_id' @ RegexMatch(r'\d+'))],
        decorators=[GroupPermission.require(GroupPermission.BOT_ADMIN), require_disable(channel.module)],
    )
)
async def unload_module(group: Group, module_id: RegexResult):
    if module_id.result is None:
        return
    target_module = await get_channel(module_id.result.display, group)
    if target_module is None:
        return
    if not target_module.meta.get('can_disable', True):
        await group.send_message(MessageChain(Plain('你指定的模块不允许禁用或卸载')))
        return
    logger.debug(f'原channels: {saya.channels}')
    logger.debug(f'要卸载的channel: {saya.channels["modules.BiliVideoInfo"]}')
    logger.info(f'卸载模块: {target_module.name} —— {target_module.module}')
    try:
        saya.uninstall_channel(saya.channels[target_module.module])
    except Exception as e:
        await group.send_message(MessageChain(Plain(f'卸载模块 {target_module.module} 时出错')))
        logger.error(f'卸载模块 {target_module.module} 时出错')
        logger.exception(e)
    else:
        logger.debug(f'卸载后的channels: {saya.channels}')
        await group.send_message(MessageChain(Plain(f'卸载模块 {target_module.module} 成功')))
