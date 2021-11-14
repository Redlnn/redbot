#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from asyncio import Lock

import yaml
from loguru import logger

if not os.path.exists('config.yml') and os.path.exists('config.exp.yml'):
    logger.error('请复制一份 config.exp.yml 并将其重命名为 config.yml 作为配置文件！')
    exit()
elif not os.path.exists('config.yml') and not os.path.exists('config.exp.yml'):
    logger.error('在？宁的配置呢?¿?¿')
    exit()
else:
    with open('config.yml', 'r', encoding='utf-8') as fr:
        file_data = fr.read()
    config_data = yaml.load(file_data, Loader=yaml.FullLoader)
    del file_data

lock = Lock()


def save_config():
    global config_data
    logger.info('正在保存配置文件...')
    with open('config.yml', 'w', encoding='utf-8') as fw:
        yaml.dump(config_data, fw, allow_unicode=True, sort_keys=False)


def reload_config():
    global config_data
    logger.info('正在重新加载配置文件...')
    try:
        with open('config.yml', 'r', encoding='utf-8') as fr1:
            file_data1 = fr1.read()
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
