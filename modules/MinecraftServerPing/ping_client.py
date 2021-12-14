#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

# import regex as re
from graia.ariadne.util.async_exec import io_bound
from mctools import PINGClient

from .dns_resolver import dns_resolver_srv

__all__ = ['ping']


@io_bound
def ping(ip: Optional[str] = None, url: Optional[str] = None, port: Optional[int] = None) -> dict:
    if not ip and not url:
        raise ValueError('Neither IP nor URL exists')
    elif ip and url:
        raise ValueError('Both IP and URL exist')

    if ip:
        host = ip
        target_port = port if port else 25565
    elif url and port:
        host = url
        target_port = port
    else:  # url and not port
        host, port = dns_resolver_srv(url)
        if not host:
            host = url
            # host = dns_resolver(url)
            # if not host:
            #     return {}
        target_port = port if port else 25565

    client = PINGClient(host=host, port=target_port, format_method=2, timeout=5)
    stats: dict = client.get_stats()
    client.stop()
    # motd: str = re.sub(r'\x1b\[[0-9]{1,3}[;]?[0-9]?m', '', stats['description'])

    if stats['players'].get('sample'):
        player_list: list = stats['players'].get('sample')
    else:
        player_list = []

    return {
        'version': str(stats['version']['name']),
        'protocol': str(stats['version']['protocol']),
        'motd': stats['description'],
        'delay': str(round(stats['time'], 1)),
        'online_player': str(stats['players']['online']),
        'max_player': str(stats['players']['max']),
        'player_list': player_list,
    }
