#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Tuple

import dns.resolver
from dns.rdatatype import RdataType
from dns.resolver import NXDOMAIN, NoAnswer

__all__ = ["domain_resolver", "domain_resolver_srv"]


# A 记录或 CNAME 记录
def domain_resolver(domain: str) -> bool | str:
    dns_resolver = dns.resolver.Resolver()
    dns_resolver.nameservers = ['119.29.29.29']
    try:
        resolve_result = dns_resolver.resolve(domain, 'A', tcp=True, lifetime=5)
    except (NoAnswer, NXDOMAIN):
        return False
    return resolve_result[0].to_text()


def domain_resolver_srv(domain: str) -> Tuple[bool | str, bool | int]:
    srv_domain = f'_minecraft._tcp.{domain}'
    dns_resolver = dns.resolver.Resolver()
    dns_resolver.nameservers = ['119.29.29.29']
    try:
        resolve_result = dns_resolver.resolve(srv_domain, 'SRV', tcp=True, lifetime=5)
    except (NoAnswer, NXDOMAIN):
        return False, False
    if resolve_result.rdtype == RdataType.SRV:
        host: str = resolve_result[0].target.to_text().strip('.')
        port: int = resolve_result[0].port
        return host, port
    return False, False
