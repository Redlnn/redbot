"""
Ping mc服务器

获取指定mc服务器的信息

> 命令：/ping [mc服务器地址]
"""

import socket
from dataclasses import field

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.message.parser.twilight import RegexMatch, RegexResult, Twilight
from graia.ariadne.model import Group
from graia.saya import Channel
from graiax.shortcut.saya import decorate, dispatch, listen
from kayaku import config, create
from loguru import logger

from libs.control import require_disable
from libs.control.interval import MemberInterval
from libs.control.permission import GroupPermission

from .ping_client import ping
from .utils import is_domain, is_ip

channel = Channel.current()

channel.meta['name'] = 'Ping 我的世界服务器'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = '获取指定mc服务器的信息\n用法：\n[!！.]ping {mc服务器地址}'


@config(channel.module)
class McServerPingConfig:
    servers: dict[str, str] = field(default_factory=lambda: {'123456789': 'localhost:25565'})
    """指定群组的默认服务器"""


ping_cfg = create(McServerPingConfig)


@listen(GroupMessage)
@dispatch(Twilight(RegexMatch(r'[!！.]ping'), 'ping_target' @ RegexMatch(r'\S+', optional=True)))
@decorate(GroupPermission.require(), MemberInterval.require(10), require_disable(channel.module))
async def main(app: Ariadne, group: Group, ping_target: RegexResult):
    if ping_target.matched and ping_target.result is not None:
        server_address = str(ping_target.result).strip()
    else:
        if str(group.id) not in ping_cfg.servers:
            await app.send_message(group, MessageChain(Plain('该群组没有设置默认服务器地址')))
            return
        server_address = ping_cfg.servers[str(group.id)]

    if '://' in server_address:
        await app.send_message(group, MessageChain(Plain('不支持带有协议前缀的地址')))
        return
    elif '/' in server_address:
        await app.send_message(group, MessageChain(Plain('ping目标地址出现意外字符')))
        return

    if is_ip(server_address):
        kwargs = {'ip': server_address}
    elif ':' in server_address:
        host, port = server_address.split(':', 1)
        if is_ip(host) or is_domain(host):
            if port.isdigit():
                kwargs = {'url': host, 'port': int(port)}
            else:
                await app.send_message(group, MessageChain(Plain('端口号格式不正确')))
                return
        else:
            await app.send_message(group, MessageChain(Plain('目标地址不是一个有效的域名或IP（不支持中文域名）')))
            return
    elif is_domain(server_address):
        kwargs = {'url': server_address}
    else:
        await app.send_message(group, MessageChain(Plain('目标地址不是一个有效的域名或IP（不支持中文域名）')))
        return

    try:
        ping_result = await ping(**kwargs)
    except ConnectionRefusedError:
        await app.send_message(group, MessageChain(Plain('连接被目标拒绝，该地址（及端口）可能不存在 Minecraft 服务器')))
        logger.warning(f'连接被目标拒绝，该地址（及端口）可能不存在Minecraft服务器，目标地址：{server_address}')
        return
    except socket.timeout:
        await app.send_message(group, MessageChain(Plain('连接超时')))
        logger.warning(f'连接超时，目标地址：{server_address}')
        return
    except socket.gaierror as e:
        await app.send_message(group, MessageChain(Plain('出错了，可能是无法解析目标地址\n' + str(e))))
        logger.exception(e)
        return

    if not ping_result:
        await app.send_message(group, MessageChain(Plain('无法解析目标地址')))
        return

    if ping_result['motd'] is not None and ping_result['motd'] != '':
        motd_list: list[str] = ping_result['motd'].split('\n')
        motd = f' | {motd_list[0].strip()}'
        if len(motd_list) == 2:
            motd += f'\n | {motd_list[1].strip()}'
    else:
        motd = None
    msg_send = f'咕咕咕！🎉\n服务器版本: [{ping_result["protocol"]}] {ping_result["version"]}\n'
    msg_send += f'MOTD:\n{motd}\n' if motd is not None else ''
    msg_send += f'延迟: {ping_result["delay"]}ms\n在线人数: {ping_result["online_player"]}/{ping_result["max_player"]}'
    if ping_result['online_player'] != '0' and ping_result['player_list']:
        players_list = ''.join(f' | {_["name"]}\n' for _ in ping_result['player_list'])
        if int(ping_result['online_player']) != len(ping_result['player_list']):
            msg_send += f'\n在线列表：\n{players_list.rstrip()}\n | ...'
        else:
            msg_send += f'\n在线列表：\n{players_list.rstrip()}'

    await app.send_message(group, MessageChain(Plain(msg_send)))
