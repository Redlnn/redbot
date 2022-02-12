#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

import orjson
from pydantic import AnyHttpUrl, BaseModel

from .path import config_path, data_path


class RConfig(BaseModel):
    __filename__: str  # 无需指定后缀
    __in_data_folder__: bool = False

    def __init__(self, **data) -> None:
        if self.__in_data_folder__:
            path = Path(data_path, f'{self.__filename__}.json')
        else:
            path = Path(config_path, f'{self.__filename__}.json')
        if not path.exists():
            super().__init__(**data)
            with open(path, 'w') as f:
                f.write(self.json(indent=2, ensure_ascii=False))
        else:
            with open(path, 'rb') as fb:
                data = orjson.loads(fb.read())
            super().__init__(**data)

    def save(self) -> None:
        if self.__in_data_folder__:
            path = Path(data_path, f'{self.__filename__}.json')
        else:
            path = Path(config_path, f'{self.__filename__}.json')
        with open(path, 'w') as f:
            f.write(self.json(indent=2, ensure_ascii=False))

    def reload(self) -> None:
        if self.__in_data_folder__:
            path = Path(data_path, f'{self.__filename__}.json')
        else:
            path = Path(config_path, f'{self.__filename__}.json')
        with open(path, 'rb') as fb:
            data = orjson.loads(fb.read())
        super().__init__(**data)


class MAHConfig(BaseModel):
    account: int
    host: AnyHttpUrl = 'http://localhost:8080'
    verifyKey: str


class AdminConfig(BaseModel):
    masterId: int = 731347477  # 机器人主人的QQ号
    masterName: str = 'Red_lnn'
    admins: list[int] = [731347477]


class BasicConfig(RConfig):
    __filename__: str = 'redbot'
    botName: str = 'redbot'
    logChat: bool = True
    console: bool = False
    debug: bool = False
    miraiApiHttp: MAHConfig = MAHConfig(account=123456789, verifyKey='VerifyKey')
    admin: AdminConfig = AdminConfig()


class ModulesConfig(RConfig):
    __filename__: str = 'modules'
    enabled: bool = True  # 是否允许加载模块
    globalDisabledModules: list[str] = []  # 全局禁用的模块列表
    disabledGroups: dict[str, list[int]] = {'BotManage': [123456789, 123456780]}  # 分群禁用模块的列表


basic_cfg = BasicConfig()
modules_cfg = ModulesConfig()
