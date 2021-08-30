#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib
import os
import traceback

import regex

from .logger import logger


class Plugin:
    __End__: bool = None

    def __init__(self, module, name=None, usage=None):
        self.name = name  # 模块名
        self.usage = usage  # 模块说明
        if hasattr(module.__init__, '__annotations__'):  # 如果模块有定义 __init__ 函数，则调用它以初始化模块
            module.__init__(**module.__init__.__annotations__)
        self.module = module  # 模块对象

    def __end__(self, *args, **kwargs):
        if hasattr(self.module, '__end__'):
            try:
                self.module.__end__(
                    *args, **self.module.__end__.__annotations__
                )
            except:  # noqa
                logger.error(f'插件异常关闭: ↓\n{traceback.format_exc()}')
                self.__End__ = False
            else:
                logger.info(f'插件 {self.name} 正常关闭')
                self.__End__ = True


_plugins = set()


def load_plugin(module_name: str) -> bool:
    """
    加载模块作为插件。

    :param module_name: 导入模块的名称
    :return: 成功与否
    """
    try:
        module = importlib.import_module(module_name)
        name = getattr(
            module, '__plugin_name__', getattr(module, '__name__', None)
        )
        usage = getattr(
            module, '__plugin_usage__', getattr(module, '__usage__', None)
        )
        _plugins.add(Plugin(module, name, usage))
        logger.info(f'加载插件 "{module_name if name is None else name}" 成功')
        return name
    except Exception: # noqa
        logger.error(f'加载插件时出错: ↓\n{traceback.format_exc()}')
        return False


def load_plugins(plugin_dir: str, module_prefix: str) -> int:
    """
    在给定目录中查找所有非隐藏的模块或软件包，并使用给定的模块前缀将其导入。

    :param plugin_dir: 搜索的插件目录
    :param module_prefix: 导入时使用的模块前缀
    :return: 成功加载的插件数量
    """
    def fors(plugin_dir, module_prefix: str):
        _plugin_dir = os.listdir(plugin_dir)
        if len(_plugin_dir) > 0:
            nonlocal count
            tmp_modules = []
            for name in _plugin_dir:
                path = os.path.join(plugin_dir, name)
                if os.path.isfile(path) and \
                        (name[0] in ('_', '!', '.', '#') or not name.endswith('.py')):
                    continue
                elif os.path.isdir(path) and \
                        (name[0] in ('_', '!', '.', '#') or not os.path.exists(os.path.join(path, '__init__.py'))):
                    continue

                m = regex.match(r'([_A-Z0-9a-z]+)(.py)?', name)
                if not m:
                    continue

                module_name = load_plugin(f'{module_prefix}.{m.group(1)}')
                if module_name:
                    if module_name in tmp_modules:
                        logger.warning(f'发现重名插件 "{module_name}"，请检查')
                    tmp_modules.append(module_name)
                    count += 1
            del tmp_modules

    count = 0
    fors(plugin_dir, module_prefix)
    logger.info(f'共加载 {count} 个插件')
    return count


def load_builtin_plugins() -> int:
    """
    加载与 "MiraiBot" 软件包一起分发的内置插件。
    """
    return load_plugins(os.path.join(os.path.dirname(__file__), 'plugins'), 'miraibot.plugins')


def get_loaded_plugins() -> object:
    """
    加载所有插件。

    :return: 一组插件对象
    """
    return _plugins
