import asyncio
from typing import Literal

import aiodns
from aiodns.error import DNSError

resolver = aiodns.DNSResolver(loop=asyncio.get_event_loop(), nameservers=['119.29.29.29'])


async def dns_resolver(domain: str) -> bool | str:
    try:
        result = await resolver.query(domain, 'A')
        return result[0].host
    except DNSError:
        return False


async def dns_resolver_srv(domain: str) -> tuple[Literal[False] | str, Literal[False] | int]:
    try:
        result = await resolver.query(f'_minecraft._tcp.{domain}', 'SRV')
        return result[0].host, result[0].port
    except DNSError:
        return False, False
