#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass

# 服务器群群号
server_group: int = 12345678

# 其他要生效的群组，若为空，即()，则仅在服务器群生效
# 格式为：active_groups = [123456, 456789, 789012]
active_groups = []


@dataclass
class RconConfig:
    server: str = 'localhost'
    port: int = 25575
    passwd: str = 'password'


@dataclass
class DatabaseConfig:
    mysql: bool = False
    mysql_database: str = 'bot'  # 数据库名称
    mysql_host: str = 'localhost'
    mysql_port: int = 3306
    mysql_user: str = 'user'
    mysql_passwd: str = 'password'
