#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from asyncio import Lock
from pathlib import Path

import yaml
from loguru import logger

if not Path.exists(Path(Path.cwd(), 'config.yml')) and Path.exists(Path(Path.cwd(), 'config.exp.yml')):
    logger.error('请复制一份 config.exp.yml 并将其重命名为 config.yml 作为配置文件！')
    exit()
elif not Path.exists(Path(Path.cwd(), 'config.yml')) and not Path.exists(Path(Path.cwd(), 'config.exp.yml')):
    logger.error('在？宁的配置呢?¿?¿')
    exit()
else:
    with open('config.yml', 'r', encoding='utf-8') as fp:
        file_data = fp.read()
    config_data = yaml.load(file_data, Loader=yaml.FullLoader)
    del file_data

lock = Lock()


def save_config():
    global config_data
    logger.info('正在保存配置文件...')
    with open('config.yml', 'w', encoding='utf-8') as fp:
        yaml.dump(config_data, fp, allow_unicode=True, sort_keys=False)


def reload_config():
    global config_data
    logger.info('正在重新加载配置文件...')
    try:
        with open('config.yml', 'r', encoding='utf-8') as fp:
            file_data1 = fp.read()
        new_data = yaml.load(file_data1, Loader=yaml.FullLoader)
        # 若直接重新赋值 config_data，会导致其内存地址发生改变，无法影响其他 import 了 config_data 的模块
        # 因此需要直接改变其内部的内容
        for key in config_data.keys():
            config_data[key] = new_data[key]
        del file_data1, new_data
        logger.info('重新加载配置文件完成')
        return True
    except Exception as e:
        logger.error('重新加载配置文件时出错')
        logger.exception(e)
        return False
