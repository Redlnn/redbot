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

from pathlib import Path

__all__ = ['root_path', 'config_path', 'logs_path', 'modules_path', 'data_path']

root_path: Path = Path(__file__).parent.parent.resolve()
config_path: Path = Path(root_path, 'config')
logs_path: Path = Path(root_path, 'logs')
modules_path: Path = Path(root_path, 'modules')
data_path: Path = Path(root_path, 'data')

config_path.mkdir(parents=True, exist_ok=True)
logs_path.mkdir(parents=True, exist_ok=True)
modules_path.mkdir(parents=True, exist_ok=True)
data_path.mkdir(parents=True, exist_ok=True)
