#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

import yaml

from utils.logger import logger

if not os.path.exists('config.yml') and os.path.exists('config.exp.yml'):
    logger.error('请复制一份 config.exp.yml 并将其重命名为 config.yml 作为配置文件！')
    exit()
elif not os.path.exists('config.yml') and not os.path.exists('config.exp.yml'):
    logger.error('在？宁的配置呢?¿?¿')
    exit()
else:
    with open('config.yml', 'r', encoding='utf-8') as f:
        file_data = f.read()
    config_data = yaml.load(file_data, Loader=yaml.FullLoader)
