#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Tuple

import aiodns
from aiodns.error import DNSError
from graia.saya import Saya

__all__ = ['dns_resolver', 'dns_resolver_srv']

resolver = aiodns.DNSResolver(loop=Saya.current().broadcast.loop, nameservers=['119.29.29.29'])


async def dns_resolver(domain: str) -> bool | str:
    try:
        result = await resolver.query(domain, 'A')
        return result[0].host
    except DNSError:
        return False


async def dns_resolver_srv(domain: str) -> Tuple[bool | str, bool | int]:
    try:
        result = await resolver.query(f'_minecraft._tcp.{domain}', 'SRV')
        return result[0].host, result[0].port
    except DNSError:
        return False, False