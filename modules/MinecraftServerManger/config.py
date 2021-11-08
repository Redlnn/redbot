#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass

active_group: tuple = (228573653,)


@dataclass
class RconConfig:
    server: str = 'localhost'
    port: int = 25575
    passwd: str = 'password'


@dataclass
class DatabaseConfig:
    database: str = 'players_list'  # 数据库名称
    mysql: bool = False
    mysql_host: str = 'localhost'
    mysql_port: int = 3306
    mysql_user: str = 'user'
    mysql_passwd: str = 'password'
