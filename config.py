#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from miraibot.default_config import *  # noqa

HOST: str = '127.0.0.1'  # 必填
PORT: int = 25567  # 必填
DEBUG: bool = False
AUTHKEY: str = 'funnyguy'  # 如果没有设置则 mirai-api-http 会随机生成它，请自行从控制台或 mirai-api-http 的配置文件中获取

ACCOUNT: int = 242679293  # 必填
ENABLE_CHAT_LOG: bool = False
