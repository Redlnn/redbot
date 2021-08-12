#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
默认配置。

任何派生的配置都必须在代码开始时从该模块导入所有内容，然后设置自己的值以覆盖默认值。

例如:

>>> from miraibot.default_config import *
>>> PORT = 9090
>>> DEBUG = False
>>> SUPERUSERS.add(123456)
>>> NICKNAME = '小明'
"""

API_ROOT: str = ''
AUTHKEY: str = None
SECRET: str = ''
HOST: str = None
PORT: int = None
DEBUG: bool = False
ACCOUNT: int = 123456
ENABLE_CHAT_LOG: bool = False

# redis连接池配置
REDIS = False  # 如果需要启用 aioredis 请在自己的配置中将这项覆盖为 True
REDIS_HOST: str = "127.0.0.1"
REDIS_PORT: int = 6379
REDIS_PASSWORD: str or None = None
REDIS_DB: int = None
REDIS_ENCODING = None
REDIS_MINSIZE: int = 1
REDIS_MAXSIZE: int = 10
