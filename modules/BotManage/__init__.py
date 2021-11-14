#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bot 管理
包含 分群配置 插件配置更改 菜单
"""

import asyncio
import os
from asyncio import Lock
from typing import List

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Plain
from graia.ariadne.message.parser.pattern import RegexMatch
from graia.ariadne.message.parser.twilight import Sparkle, Twilight
from graia.ariadne.model import Group, Member, MemberPerm
from graia.broadcast.interrupt import InterruptControl
from graia.broadcast.interrupt.waiter import Waiter
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger

from config import config_data, reload_config, save_config
from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Permission import Permission
from utils.Limit.Rate import GroupInterval
from utils.ModuleRegister import Module, Modules
from utils.TextWithImg2Img import reload_config as gen_img_reload

from .TextWithImg2Img import async_generate_img, hr

lock: Lock = Lock()
saya = Saya.current()
channel = Channel.current()
inc = InterruptControl(saya.broadcast)

# ensp = ' '  # 半角空格
# emsp = ' '  # 全角空格

Module(
    name='Bot模块管理',
    config_name='BotManage',
    file_name=os.path.dirname(__file__),
    author=['Red_lnn'],
    description='管理Bot已加载的模块',
    usage=(
        '[!！.](菜单|menu) —— 获取模块列表\n'
        '[!！.]启用模块 <模块ID> —— 【管理员】启用某个已禁用的模块（全局禁用除外）\n'
        '[!！.]禁用模块 <模块ID> —— 【管理员】禁用某个已启用的模块（禁止禁用的模块除外）\n'
        '[!！.]重载配置 —— 【Bot管理员】重载Bot和模块的配置文件（不影响部分模块）\n'
        '[!！.]重载模块 <模块ID> —— 【Bot管理员，强烈不推荐】重载指定模块\n'
        '[!！.]加载模块 <模块文件名> —— 【Bot管理员】加载新模块（文件名无需后缀）\n'
        '[!！.]卸载模块 <模块ID> —— 【Bot管理员，强烈不推荐】卸载指定模块\n'
    ),
    can_disable=False,
).register()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.](菜单|menu)')]))],
        # decorators=[group_blacklist(), GroupInterval.require(5)],
    )
)
async def menu(app: Ariadne, group: Group):
    if not config_data['Modules']['BotManage']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['BotManage']['DisabledGroup']:
        if group.id in config_data['Modules']['BotManage']['DisabledGroup']:
            return
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
            status = '【全局禁用】'
        elif group.id in disabled_groups:
            status = '【本群禁用】'
        else:
            status = '  【启用】  '
        msg_send += f'{num}. {status}  {module.name}\n'
    msg_send += (
        f'{hr}\n'
        f'私は {config_data["Basic"]["Permission"]["MasterName"]} の {config_data["Basic"]["BotName"]} です www\n'
        '群管理员要想配置模块开关请发送【.启用/禁用模块 <id>】\n'
        '要想查询某模块的用法和介绍请发送【.用法 <id>】\n'
        '若无法触发，请检查前缀符号是否正确如 ! 与 ！\n'
        '或是命令中有无多余空格，所有模块均不需要@bot\n'
        '全局禁用的模块不能重新开启\n'
    )
    img_io = await async_generate_img([msg_send])
    await app.sendGroupMessage(group, MessageChain.create(Image(data_bytes=img_io.getvalue())))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]启用模块\ '), RegexMatch(r'\d+')]))],
        decorators=[group_blacklist(), GroupInterval.require(5), Permission.group_perm_check(MemberPerm.Administrator)],
    )
)
async def turn_on(app: Ariadne, group: Group, sparkle: Sparkle):
    if not config_data['Modules']['BotManage']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['BotManage']['DisabledGroup']:
        if group.id in config_data['Modules']['BotManage']['DisabledGroup']:
            return
    target_id = int(sparkle._check_1.result.asDisplay()) - 1
    if target_id >= len(Modules):
        await app.sendGroupMessage(group, MessageChain.create(Plain('你指定的模块不存在')))
    target_module: Module = Modules[target_id]
    global_disabled: bool = not config_data['Modules'][target_module.config_name]['Enabled']
    disabled_groups: List[int] = config_data['Modules'][target_module.config_name]['DisabledGroup']
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
        decorators=[group_blacklist(), GroupInterval.require(5), Permission.group_perm_check(MemberPerm.Administrator)],
    )
)
async def turn_off(app: Ariadne, group: Group, sparkle: Sparkle):
    if not config_data['Modules']['BotManage']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['BotManage']['DisabledGroup']:
        if group.id in config_data['Modules']['BotManage']['DisabledGroup']:
            return
    target_id = int(sparkle._check_1.result.asDisplay()) - 1
    if target_id >= len(Modules):
        await app.sendGroupMessage(group, MessageChain.create(Plain('你指定的模块不存在')))
    target_module: Module = Modules[target_id]
    disabled_groups: List[int] = config_data['Modules'][target_module.config_name]['DisabledGroup']
    if not target_module.can_disable:
        await app.sendGroupMessage(group, MessageChain.create(Plain('你指定的模块不允许禁用')))
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
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]用法\ '), RegexMatch(r'\d+')]))],
        decorators=[group_blacklist(), GroupInterval.require(5), Permission.group_perm_check(MemberPerm.Administrator)],
    )
)
async def turn_off(app: Ariadne, group: Group, sparkle: Sparkle):
    if not config_data['Modules']['BotManage']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['BotManage']['DisabledGroup']:
        if group.id in config_data['Modules']['BotManage']['DisabledGroup']:
            return
    target_id = int(sparkle._check_1.result.asDisplay()) - 1
    if target_id >= len(Modules):
        await app.sendGroupMessage(group, MessageChain.create(Plain('你指定的模块不存在')))
    target_module: Module = Modules[target_id]
    disabled_groups: List[int] = config_data['Modules'][target_module.config_name]['DisabledGroup']
    if group.id in disabled_groups:
        await app.sendGroupMessage(group, MessageChain.create(Plain('该模块已在本群禁用')))
        return
    authors = ''
    if target_module.author:
        for author in target_module.author:
            authors += author + ', '
        authors = authors.rstrip(', ')
    msg_send = f'{target_module.name}{" By " + authors if authors else ""}\n\n'
    if target_module.description:
        msg_send += '>>>>>>>>>>>>>>>>>>>>> 模块描述 <<<<<<<<<<<<<<<<<<<<<\n' + target_module.description + '\n\n'
    if target_module.usage:
        msg_send += '>>>>>>>>>>>>>>>>>>>>> 模块用法 <<<<<<<<<<<<<<<<<<<<<\n' + target_module.usage + '\n\n'
    if target_module.arg_description:
        msg_send += '>>>>>>>>>>>>>>>>>>>>> 参数介绍 <<<<<<<<<<<<<<<<<<<<<\n' + target_module.arg_description
    img_io = await async_generate_img([msg_send])
    await app.sendGroupMessage(group, MessageChain.create(Image(data_bytes=img_io.getvalue())))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]重载配置')]))],
        decorators=[group_blacklist(), GroupInterval.require(5), Permission.group_perm_check(Permission.BOT_ADMIN)],
    )
)
async def reload_bot_and_modules_config(app: Ariadne, group: Group):
    if not config_data['Modules']['BotManage']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['BotManage']['DisabledGroup']:
        if group.id in config_data['Modules']['BotManage']['DisabledGroup']:
            return
    async with lock:
        await app.sendGroupMessage(group, MessageChain.create(Plain('重新加载配置文件中...（若无下一步提示即加载完成）')))
        if reload_config():
            try:
                gen_img_reload()
            except Exception as e:
                await app.sendGroupMessage(group, MessageChain.create(Plain(f'重新加载文本图像转图片的配置文件时出错，错误内容：{e}')))
            return
        else:
            await app.sendGroupMessage(group, MessageChain.create(Plain('重新加载配置文件时出错')))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]重载模块\ '), RegexMatch(r'\d+')]))],
        decorators=[group_blacklist(), GroupInterval.require(5), Permission.group_perm_check(Permission.BOT_ADMIN)],
    )
)
async def reload_module(app: Ariadne, group: Group, member: Member, sparkle: Sparkle):
    if not config_data['Modules']['BotManage']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['BotManage']['DisabledGroup']:
        if group.id in config_data['Modules']['BotManage']['DisabledGroup']:
            return

    @Waiter.create_using_function([GroupMessage])
    async def waiter(waiter_group: Group, waiter_member: Member, waiter_message: MessageChain):
        if waiter_group.id == group.id and waiter_member.id == member.id:
            saying = waiter_message.asDisplay()
            if saying == '.force':
                return True
            elif saying == '.cancel':
                return False
            else:
                await app.sendGroupMessage(group, MessageChain.create(At(member.id), Plain('请发送 .force 或 .cancel')))

    # 重载即卸载重新加载，在加载含有 `saya = Saya.current()` 的模块时 100% 报错
    await app.sendGroupMessage(
        group,
        MessageChain.create(
            At(member.id), Plain('重载模块有极大可能会出错且只有重启bot才能恢复，请问你确实要重载吗？\n' '强制重载请在10s发送 .force ，取消请发送 .cancel')
        ),
    )
    answer = await asyncio.wait_for(inc.wait(waiter), timeout=10)
    if not answer:
        await app.sendGroupMessage(group, MessageChain.create(Plain('已取消')))

    target_id = int(sparkle._check_1.result.asDisplay()) - 1
    if target_id >= len(Modules):
        await app.sendGroupMessage(group, MessageChain.create(Plain('你指定的模块不存在')))
    target_module: Module = Modules[target_id]
    target_filename = target_module.file_name if target_module.file_name[-3:] != '.py' else target_module.file_name[:-3]
    logger.info(f'重载模块: {target_module.name} —— modules.{target_filename}')
    try:
        saya.reload_channel(saya.channels[f'modules.{target_filename}'])
    except Exception as e:
        await app.sendGroupMessage(group, MessageChain.create(Plain(f'重载模块 modules.{target_filename} 时出错')))
        Modules.remove(target_module)
        logger.error(f'重载模块 modules.{target_filename} 时出错')
        logger.exception(e)
    else:
        await app.sendGroupMessage(group, MessageChain.create(Plain(f'重载模块 modules.{target_filename} 成功')))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]加载模块\ '), RegexMatch(r'.+')]))],
        decorators=[group_blacklist(), GroupInterval.require(5), Permission.group_perm_check(Permission.BOT_ADMIN)],
    )
)
async def load_module(app: Ariadne, group: Group, member: Member, sparkle: Sparkle):
    if not config_data['Modules']['BotManage']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['BotManage']['DisabledGroup']:
        if group.id in config_data['Modules']['BotManage']['DisabledGroup']:
            return

    @Waiter.create_using_function([GroupMessage])
    async def waiter(waiter_group: Group, waiter_member: Member, waiter_message: MessageChain):
        if waiter_group.id == group.id and waiter_member.id == member.id:
            saying = waiter_message.asDisplay()
            if saying == '.force':
                return True
            elif saying == '.cancel':
                return False
            else:
                await app.sendGroupMessage(group, MessageChain.create(At(member.id), Plain('请发送 .force 或 .cancel')))

    # 在加载含有 `saya = Saya.current()` 的模块时 100% 报错
    await app.sendGroupMessage(
        group, MessageChain.create(At(member.id), Plain('加载新模块有极大可能会出错，请问你确实吗？\n' '强制加载请在10s发送 .force ，取消请发送 .cancel'))
    )
    answer = await asyncio.wait_for(inc.wait(waiter), timeout=10)
    if not answer:
        await app.sendGroupMessage(group, MessageChain.create(Plain('已取消')))
    match_result = sparkle._check_1.result.asDisplay()
    target_filename = match_result if match_result[-3:] != '.py' else match_result[:-3]
    modules_dir_list = os.listdir(os.path.join(os.getcwd(), 'modules'))
    if target_filename + '.py' in modules_dir_list or target_filename in modules_dir_list:
        try:
            saya.require('modules.' + target_filename)
        except Exception as e:
            await app.sendGroupMessage(group, MessageChain.create(Plain(f'加载模块 modules.{target_filename} 时出错')))
            logger.error(f'加载模块 modules.{target_filename} 时出错')
            logger.exception(e)
            return
        else:
            await app.sendGroupMessage(group, MessageChain.create(Plain(f'加载模块 modules.{target_filename} 成功')))
            return
    else:
        await app.sendGroupMessage(group, MessageChain.create(Plain(f'模块 modules.{target_filename} 不存在')))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.]卸载模块\ '), RegexMatch(r'\d+')]))],
        decorators=[group_blacklist(), GroupInterval.require(5), Permission.group_perm_check(Permission.BOT_ADMIN)],
    )
)
async def unload_module(app: Ariadne, group: Group, sparkle: Sparkle):
    if not config_data['Modules']['BotManage']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['BotManage']['DisabledGroup']:
        if group.id in config_data['Modules']['BotManage']['DisabledGroup']:
            return
    target_id = int(sparkle._check_1.result.asDisplay()) - 1
    if target_id >= len(Modules):
        await app.sendGroupMessage(group, MessageChain.create(Plain('你指定的模块不存在')))
    target_module: Module = Modules[target_id]
    if not target_module.can_disable:
        await app.sendGroupMessage(group, MessageChain.create(Plain('你指定的模块不允许禁用或卸载')))
        return
    target_filename = target_module.file_name if target_module.file_name[-3:] != '.py' else target_module.file_name[:-3]
    logger.debug(f'原channels: {saya.channels}')
    logger.debug(f'要卸载的channel: {saya.channels["modules.BiliVideoInfo"]}')
    logger.info(f'卸载模块: {target_module.name} —— modules.{target_filename}')
    try:
        saya.uninstall_channel(saya.channels[f'modules.{target_filename}'])
    except Exception as e:
        await app.sendGroupMessage(group, MessageChain.create(Plain(f'卸载模块 modules.{target_filename} 时出错')))
        Modules.remove(target_module)
        logger.error(f'卸载模块 modules.{target_filename} 时出错')
        logger.exception(e)
    else:
        logger.debug(f'卸载后的channels: {saya.channels}')
        await app.sendGroupMessage(group, MessageChain.create(Plain(f'卸载模块 modules.{target_filename} 成功')))
        Modules.remove(target_module)
