from util.better_pydantic import BaseModel
from util.config import RConfig


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


class McServerMangerConfig(RConfig):
    __filename__: str = 'mc_server_manager'
    serverGroup: int = 123456789  # 服务器群群号
    activeGroups: list[int] = [123456789]
    rcon: RconConfig = RconConfig()
    database: DatabaseConfig = DatabaseConfig()


config = McServerMangerConfig()

if config.serverGroup not in config.activeGroups:
    config.activeGroups.append(config.serverGroup)
    config.save()
