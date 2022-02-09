#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pydantic import BaseModel

from util.config import get_config, save_config


class RconConfig(BaseModel):
    host: str = 'localhost'
    port: int = 25575
    passwd: str = 'password'


class DatabaseConfig(BaseModel):
    enableMySQL: bool = False
    database: str = 'redbot'
    host: str = 'localhost'
    port: int = 3306
    user: str = 'user'
    passwd: str = 'password'


class McServerMangerConfig(BaseModel):
    serverGroup: int = 123456789  # 服务器群群号
    activeGroups: list[int] = [123456789]
    rcon: RconConfig = RconConfig()
    database: DatabaseConfig = DatabaseConfig()


config = get_config('mc_server_manager.json', McServerMangerConfig())

if config.serverGroup not in config.activeGroups:
    config.activeGroups.append(config.serverGroup)
    save_config('mc_server_manager.json', config)
