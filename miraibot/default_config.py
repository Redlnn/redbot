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

from datetime import timedelta
from typing import Container, Union, Iterable, Pattern, Optional, Dict, Any


API_ROOT: str = ''
AUTHKEY: str = ''
SECRET: str = ''
HOST: str = '127.0.0.1'
PORT: int = 8080
DEBUG: bool = True
QQ: int = 123456
