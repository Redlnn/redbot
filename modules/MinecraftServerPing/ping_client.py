#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

import regex
from mctools import PINGClient

from .domain_resolver import domain_resolver, domain_resolver_srv

__all__ = ["ping"]


def _raw(text: bytes) -> str:
    """
    Return a raw string representation of text
    将包含字符串的 byte 流转换为普通字符串，同时删除其中的终端控制符号
    """
    trans_map = {
        '\x1b': r'\x1b',
    }
    new_str = ''
    for char in text:
        try:
            new_str += trans_map[char]  # noqa
        except KeyError:
            new_str += char
    return new_str


def ping(ip: Optional[str] = None, url: Optional[str] = None, port: Optional[int] = None):
    if not ip and not url:
        raise ValueError('Neither IP nor URL exists')
    elif ip and url:
        raise ValueError('Both IP and URL exist')

    if ip:
        target_host = ip
        target_port = port if port else 25565
    elif url and port:
        target_host = url
        target_port = port
    else:  # url and not port
        host, port = domain_resolver_srv(url)
        if not host:
            host = domain_resolver(url)
        target_host = host
        target_port = port if port else 25565

    try:
        ping = PINGClient(host=target_host, port=target_port, format_method=2, timeout=5)
        stats = ping.get_stats()
        ping.stop()
        motd = stats['description']
    except KeyError:
        ping = PINGClient(host=target_host, port=target_port, timeout=5)
        stats = ping.get_stats()
        ping.stop()
        motd = regex.sub(r'[\\]x1b[[]([0-9_;]*)m', '', _raw(stats['description']))

    version = str(stats['version']['name'])
    protocol = str(stats['version']['protocol'])
    delay = str(round(stats['time'], 1))
    online_player = str(stats['players']['online'])
    max_player = str(stats['players']['max'])

    if stats['players'].get('sample'):
        player_list: list = stats['players'].get('sample')
    else:
        player_list = []

    return {
        'version': version,
        'protocol': protocol,
        'motd': motd,
        'delay': delay,
        'online_player': online_player,
        'max_player': max_player,
        'player_list': player_list,
    }
