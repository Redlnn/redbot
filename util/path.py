#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
获取相关路径，同时自动创建必要路径

root: 根路径

config: 设置文件所在路径

logs: 日志文件所在路径

modules: 插件所在路径

data: 数据文件所在路径
"""

from os import makedirs, unlink
from os.path import abspath, dirname, exists, isfile, join

__all__ = ['root_path', 'config_path', 'logs_path', 'modules_path', 'data_path']

root_path = abspath(dirname(dirname(__file__)))
config_path = abspath(join(root_path, "config"))
logs_path = abspath(join(root_path, "logs"))
modules_path = abspath(join(root_path, "modules"))
data_path = abspath(join(root_path, "data"))

if not exists(config_path):
    makedirs(config_path)
elif isfile(config_path):
    unlink(config_path)
    makedirs(config_path)

if not exists(logs_path):
    makedirs(logs_path)
elif isfile(logs_path):
    unlink(logs_path)
    makedirs(logs_path)

if not exists(modules_path):
    makedirs(modules_path)
elif isfile(modules_path):
    unlink(modules_path)
    makedirs(modules_path)

if not exists(data_path):
    makedirs(data_path)
elif isfile(data_path):
    unlink(data_path)
    makedirs(data_path)
