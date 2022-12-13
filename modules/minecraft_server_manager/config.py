from dataclasses import dataclass, field

import kayaku
from graia.saya.channel import Channel
from kayaku import config as k_config
from kayaku import create

channel = Channel.current()


@dataclass
class RconConfig:
    host: str = 'localhost'
    """RCON 连接地址"""
    port: int = 25575
    """RCON 端口"""
    passwd: str = 'password'
    """RCON 密码"""


@dataclass
class DatabaseConfig:
    enableMySQL: bool = False
    """是否使用 MySQL"""
    database: str = 'redbot'
    """数据库名称

    当使用 SQLite 时则为文件名
    """
    host: str = 'localhost'
    """MySQL 数据库地址"""
    port: int = 3306
    """MySQL 数据库端口"""
    user: str = 'user'
    """MySQL 数据库用户"""
    passwd: str = 'password'
    """MySQL 数据库密码"""


@k_config(channel.module)
class McServerMangerConfig:
    serverGroup: int = 123456789
    """服务器群群号"""
    activeGroups: list[int] = field(default_factory=lambda: [123456789])
    """要激活功能的群组（同一服务器的不同群）"""
    rcon: RconConfig = RconConfig()
    """RCON 连接设置"""
    database: DatabaseConfig = DatabaseConfig()
    """数据库设置"""


config: McServerMangerConfig = create(McServerMangerConfig)

if config.serverGroup not in config.activeGroups:
    config.activeGroups.append(config.serverGroup)
    kayaku.save(config)
