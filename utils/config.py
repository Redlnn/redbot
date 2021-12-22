#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import mkdir, remove, unlink
from os.path import exists, isdir, isfile, join
from typing import Dict, List, TypeVar

from pydantic import AnyHttpUrl, BaseModel

from .path import config_path, data_path

T_BaseModel = TypeVar("T_BaseModel", bound=BaseModel)


class MAHConfig(BaseModel):
    account: int
    host: AnyHttpUrl = 'http://localhost:8080'
    verifyKey: str


class AdminConfig(BaseModel):
    masterId: int = 731347477  # 机器人主人的QQ号
    masterName: str = 'Red_lnn'
    admins: List[int] = [731347477]


class BasicConfig(BaseModel):
    botName: str = 'redbot'
    logChat: bool = False
    debug: bool = False
    miraiApiHttp: MAHConfig = MAHConfig(account=123456789, verifyKey='VerifyKey')
    admin: AdminConfig = AdminConfig()


class ModulesConfig(BaseModel):
    enabled: bool = True  # 是否允许加载模块
    globalDisabledModules: List[str] = []  # 全局禁用的模块列表
    disabledGroups: Dict[str, List[int]] = {'BotManage': [123456789, 123456780]}  # 分群禁用模块的列表


module_cfg: ModulesConfig


def save_config(filename: str, config_model: BaseModel, folder: str = None, in_data_folder: bool = False):
    target_path = join(data_path, folder) if in_data_folder else join(config_path)
    if folder:
        file_path = join(target_path, folder, filename)
    else:
        file_path = join(target_path, filename)
    with open(file_path, 'w', encoding='utf8') as fp:
        fp.write(config_model.json(indent=2, ensure_ascii=False))


def get_config(filename: str, config_model: BaseModel, folder: str = None, in_data_folder: bool = False) -> T_BaseModel:
    target_path = join(data_path, folder) if in_data_folder else join(config_path)
    if folder:
        folder_path = join(target_path, folder)
        if not exists(folder_path):
            mkdir(folder_path)
        elif isfile(folder_path):
            unlink(folder_path)
            mkdir(folder_path)
        file_path = join(folder_path, filename)
    else:
        file_path = join(target_path, filename)
    if not exists(file_path):
        save_config(filename, config_model)
        return config_model
    elif isdir(file_path):
        remove(file_path)
        save_config(filename, config_model)
        return config_model
    else:
        return config_model.parse_file(file_path)


def get_main_config():
    if not exists(join(config_path, 'redbot.json')):
        save_config('redbot.json', BasicConfig())
        raise ValueError('在? 爷的配置文件哪去了? 给你放了一份，改好了再叫爷!')
    else:
        basic_cfg: BasicConfig = get_config('redbot.json', BasicConfig())
        if basic_cfg.admin.masterId not in basic_cfg.admin.admins:
            basic_cfg.admin.admins.append(basic_cfg.admin.masterId)
            save_config('redbot.json', basic_cfg)
        if basic_cfg.miraiApiHttp.account == 123456789:
            raise ValueError('在?¿ 宁配置文件没改，改好了再叫爷!!!')
        return basic_cfg


def get_modules_config():
    global module_cfg
    module_cfg = get_config('modules.json', ModulesConfig())
    return module_cfg


def save_modules_config():
    save_config('modules.json', module_cfg)
