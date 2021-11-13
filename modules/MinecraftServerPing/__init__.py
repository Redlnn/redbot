#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ping mc服务器

获取指定mc服务器的信息

> 命令：/ping [mc服务器地址
"""

import asyncio
import socket

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.pattern import RegexMatch
from graia.ariadne.message.parser.twilight import Sparkle, Twilight
from graia.ariadne.model import Group
from graia.saya import Channel, Saya
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger
from requests import ConnectTimeout, ReadTimeout, Timeout
from urllib3.exceptions import TimeoutError

from config import config_data
from utils.Limit.Blacklist import group_blacklist
from utils.Limit.Rate import MemberInterval
from .ping_client import ping
from .utils import is_domain, is_ip
from ..BotManage import Module

saya = Saya.current()
channel = Channel.current()

Module(
        name='Ping 我的世界服务器',
        config_name='MinecraftServerPing',
        author=['Red_lnn'],
        description='获取指定mc服务器的信息',
        usage='[!！.]ping {mc服务器地址}'
).registe()


class Match(Sparkle):
    prefix = RegexMatch(r'[!！.]ping')
    ping_target = RegexMatch(r'\ \S+', optional=True)


@channel.use(
        ListenerSchema(
                listening_events=[GroupMessage],
                inline_dispatchers=[Twilight(Match)],
                decorators=[group_blacklist(), MemberInterval.require(10)],
        )
)
async def main(app: Ariadne, group: Group, sparkle: Sparkle):
    if not config_data['Modules']['MinecraftServerPing']['Enabled']:
        saya.uninstall_channel(channel)
        return
    elif config_data['Modules']['MinecraftServerPing']['DisabledGroup']:
        if group.id in config_data['Modules']['MinecraftServerPing']['DisabledGroup']:
            return
    servers = config_data['Modules']['MinecraftServerPing']['Servers']
    if sparkle.ping_target.matched:
        server_address = sparkle.ping_target.result.asDisplay().strip()
    else:
        if group.id not in servers.keys():
            await app.sendGroupMessage(group, MessageChain.create([Plain('该群组没有设置默认服务器地址')]))
            return
        server_address = servers[group.id]

    if '://' in server_address:
        await app.sendGroupMessage(group, MessageChain.create([Plain('不支持带有协议前缀的地址')]))
        return
    elif '/' in server_address:
        await app.sendGroupMessage(group, MessageChain.create([Plain('ping目标地址出现意外字符')]))
        return

    if is_ip(server_address):
        kwargs = {'ip': server_address}
    elif ':' in server_address:
        host, port = server_address.split(':', 1)
        if is_ip(host) or is_domain(host):
            if port.isdigit():
                kwargs = {'url': host, 'port': port}
            else:
                await app.sendGroupMessage(group, MessageChain.create([Plain('端口号格式不正确')]))
                return
        else:
            await app.sendGroupMessage(group, MessageChain.create([Plain('目标地址不是一个有效的域名或IP（不支持中文域名）')]))
            return
    elif is_domain(server_address):
        kwargs = {'url': server_address}
    else:
        await app.sendGroupMessage(group, MessageChain.create([Plain('目标地址不是一个有效的域名或IP（不支持中文域名）')]))
        return

    try:
        ping_result = await asyncio.to_thread(ping, **kwargs)
    except ConnectionRefusedError:
        await app.sendGroupMessage(group, MessageChain.create([Plain('连接被目标拒绝，该地址（及端口）可能不存在 Minecraft 服务器')]))
        logger.warning(f'连接被目标拒绝，该地址（及端口）可能不存在Minecraft服务器，目标地址：{server_address}')
        return
    except (Timeout, ReadTimeout, ConnectTimeout, TimeoutError, socket.timeout):
        await app.sendGroupMessage(group, MessageChain.create([Plain('连接超时')]))
        logger.warning(f'连接超时，目标地址：{server_address}')
        return
    except Exception as e:  # noqa
        await app.sendGroupMessage(group, MessageChain.create([Plain(f'发生错误：{e}')]))
        logger.exception(e)
        return

    motd_list = ping_result['motd'].split('\n')
    motd = f' | {motd_list[0].strip()}'
    if len(motd_list) == 2:
        motd += f'\n | {motd_list[1].strip()}'
    online_player = int(ping_result['online_player'])
    if online_player == 0:
        msg_send = (
            f'咕咕咕！！！\n'
            f'服务器版本: [{ping_result["protocol"]}] {ping_result["version"]}'
            f'MOTD:\n{motd}\n'
            f'延迟: {ping_result["delay"]}ms\n'
            f'在线人数: {ping_result["online_player"]}/{ping_result["max_player"]}\n'
            f'にゃ～'
        )
    else:
        players_list = ''
        for _ in ping_result['player_list']:
            players_list += f' | {_[0]}\n'
        if online_player <= 10:
            msg_send = (
                f'咕咕咕！！！\n'
                f'服务器版本: [{ping_result["protocol"]}] {ping_result["version"]}\n'
                f'MOTD:\n{motd}\n'
                f'延迟: {ping_result["delay"]}ms\n'
                f'在线人数: {ping_result["online_player"]}/{ping_result["max_player"]}\n'
                f'在线列表：\n{players_list}\n'
                f'にゃ～'
            )
        else:
            msg_send = (
                f'咕咕咕！！！\n'
                f'服务器版本: [{ping_result["protocol"]}] {ping_result["version"]}\n'
                f'MOTD:\n{motd}\n'
                f'延迟: {ping_result["delay"]}ms\n'
                f'在线人数: {ping_result["online_player"]}/{ping_result["max_player"]}\n'
                f'在线列表（不完整）：\n{players_list}\n'
                f'にゃ～'
            )

    await app.sendGroupMessage(group, MessageChain.create([Plain(msg_send)]))
