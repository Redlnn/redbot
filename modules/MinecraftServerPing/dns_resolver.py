#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Tuple

import dns.resolver
from dns.rdatatype import RdataType
from dns.resolver import NXDOMAIN, NoAnswer

__all__ = ['dns_resolver', 'dns_resolver_srv']


# A 记录或 CNAME 记录
def dns_resolver(domain: str) -> bool | str:
    resolver = dns.resolver.Resolver()
    try:
        resolve_result = resolver.resolve(domain, 'A', lifetime=5)
    except (NoAnswer, NXDOMAIN):
        return False
    return resolve_result[0].to_text()


def dns_resolver_srv(domain: str) -> Tuple[bool | str, bool | int]:
    resolver = dns.resolver.Resolver()
    try:
        resolve_result = resolver.resolve(f'_minecraft._tcp.{domain}', 'SRV', lifetime=5)
    except (NoAnswer, NXDOMAIN):
        return False, False
    if resolve_result.rdtype == RdataType.SRV:
        host: str = resolve_result[0].target.to_text().strip('.')
        port: int = resolve_result[0].port
        return host, port
    return False, False
