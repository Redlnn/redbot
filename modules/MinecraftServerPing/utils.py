#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import regex


def is_domain(value: str) -> bool:
    """
    Return whether or not given value is a valid domain.
    If the value is valid domain name this function returns ``True``, otherwise False
    :param value: domain string to validate
    """
    pattern = regex.compile(
        r'^(([a-zA-Z]{1})|([a-zA-Z]{1}[a-zA-Z]{1})|'
        r'([a-zA-Z]{1}[0-9]{1})|([0-9]{1}[a-zA-Z]{1})|'
        r'([a-zA-Z0-9][-_.a-zA-Z0-9]{0,61}[a-zA-Z0-9]))\.'
        r'([a-zA-Z]{2,13}|[a-zA-Z0-9-]{2,30}.[a-zA-Z]{2,3})$'
    )
    return True if pattern.match(value) else False


def is_ip(host: str) -> bool:
    return (
        True
        if regex.match(r'^((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}$', host)
        else False
    )
