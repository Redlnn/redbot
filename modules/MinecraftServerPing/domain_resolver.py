#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Tuple

import dns.resolver
from dns.rdatatype import RdataType
from dns.resolver import NXDOMAIN, NoAnswer

__all__ = ["domain_resolver", "domain_resolver_srv"]


def domain_resolver(domain: str) -> bool | str:
    dns_resolver = dns.resolver.Resolver()
    dns_resolver.nameservers = ['119.29.29.29']
    try:
        resolve_result = dns_resolver.resolve(domain, 'A', tcp=True, lifetime=5)
    except (NoAnswer, NXDOMAIN):
        return False
    nameserver_answer = resolve_result.response.answer
    target_ip = nameserver_answer[0][0].address
    return target_ip


def domain_resolver_srv(domain: str) -> Tuple[bool | str, bool | str]:
    srv_domain = f'_minecraft._tcp.{domain}'
    dns_resolver = dns.resolver.Resolver()
    dns_resolver.nameservers = ['119.29.29.29']
    try:
        resolve_result = dns_resolver.resolve(srv_domain, 'SRV', tcp=True, lifetime=5)
    except (NoAnswer, NXDOMAIN):
        return False, False
    nameserver_answer = resolve_result.response.answer
    if nameserver_answer[0][0].rdtype == RdataType.SRV:
        host = str(nameserver_answer[0][0].target).rstrip('.')
        port = nameserver_answer[0][0].port
        return host, port
    return False, False
