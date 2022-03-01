#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

import orjson
from pydantic import AnyHttpUrl, BaseModel

from .path import config_path, data_path


class RConfig(BaseModel):
    __filename__: str | None = None  # 无需指定后缀，当实例化时不传入该参数则与 BaseModel 无异
    __in_data_folder__: bool = False

    def __init__(self, **data) -> None:
        if self.__filename__ is None:
            super().__init__(**data)
            return
        elif self.__in_data_folder__:
            path = Path(data_path, f'{self.__filename__}.json')
        else:
            path = Path(config_path, f'{self.__filename__}.json')

        if not path.exists():
            super().__init__(**data)
            with open(path, 'w') as f:
                f.write(self.json(indent=2, ensure_ascii=False))
        else:
            with open(path, 'rb') as fb:
                file_data = orjson.loads(fb.read())
            if data:
                for key, item in data.items():
                    file_data[key] = item
            super().__init__(**file_data)

    def save(self) -> None:
        if self.__filename__ is None:
            raise ValueError('__filename__ is not defined')
        elif self.__in_data_folder__:
            path = Path(data_path, f'{self.__filename__}.json')
        else:
            path = Path(config_path, f'{self.__filename__}.json')
        with open(path, 'w') as f:
            f.write(self.json(indent=2, ensure_ascii=False))

    def reload(self) -> None:
        if self.__filename__ is None:
            raise ValueError('__filename__ is not defined')
        elif self.__in_data_folder__:
            path = Path(data_path, f'{self.__filename__}.json')
        else:
            path = Path(config_path, f'{self.__filename__}.json')
        with open(path, 'rb') as fb:
            data = orjson.loads(fb.read())
        super().__init__(**data)


class MAHConfig(RConfig):
    account: int
    host: AnyHttpUrl = 'http://localhost:8080'
    verifyKey: str


class AdminConfig(RConfig):
    masterId: int = 731347477  # 机器人主人的QQ号
    masterName: str = 'Red_lnn'
    admins: list[int] = [731347477]


class BasicConfig(RConfig):
    __filename__: str = 'redbot'
    botName: str = 'redbot'
    logChat: bool = True
    console: bool = False
    debug: bool = False
    databaseUrl: str = 'sqlite+aiosqlite:///data/database.db'
    # mysql+asyncmy://user:pass@hostname/dbname?charset=utf8mb4
    miraiApiHttp: MAHConfig = MAHConfig(account=123456789, verifyKey='VerifyKey')
    admin: AdminConfig = AdminConfig()


class ModulesConfig(RConfig):
    __filename__: str = 'modules'
    enabled: bool = True  # 是否允许加载模块
    globalDisabledModules: list[str] = []  # 全局禁用的模块列表
    disabledGroups: dict[str, list[int]] = {'BotManage': [123456789, 123456780]}  # 分群禁用模块的列表


basic_cfg = BasicConfig()
modules_cfg = ModulesConfig()
