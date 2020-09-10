import importlib
import os
import re

from .logger import LoggingLogger


class Plugin:
    __slots__ = ('module', 'name', 'usage')

    def __init__(self, module,
                 name=None,
                 usage=None):
        self.module = module
        self.name = name
        self.usage = usage


_plugins = set()


def load_plugin(module_name: str) -> bool:
    """
    加载模块作为插件。

    :变量 module_name: 导入模块的名称
    :return: 成功与否
    """
    try:
        module = importlib.import_module(module_name)
        name = getattr(module, '__plugin_name__', None)
        usage = getattr(module, '__plugin_usage__', None)
        _plugins.add(Plugin(module, name, usage))
        LoggingLogger.info(f'成功导入 "{module_name}"')
        return True
    except Exception as e:
        LoggingLogger.error(f'导入失败 "{module_name}", error: {e}')
        #logger.exception(e)
        return False


def load_plugins(plugin_dir: str, module_prefix: str) -> int:
    """
    在给定目录中查找所有非隐藏的模块或软件包，并使用给定的模块前缀将其导入。

    :变量 plugin_dir: 搜索的插件目录
    :变量 module_prefix: 导入时使用的模块前缀
    :return: 成功加载的插件数量
    """
    def fors(plugin_dir, module_prefix: str):
        _plugin_dir = os.listdir(plugin_dir)
        if len(_plugin_dir) > 0:
            nonlocal count
            for name in _plugin_dir:
                path = os.path.join(plugin_dir, name)
                if os.path.isfile(path) and \
                        (name.startswith('_') or not name.endswith('.py')):
                    continue
                if os.path.isdir(path) and \
                        (name.startswith('_') or not os.path.exists(
                            os.path.join(path, '__init__.py'))):
                    continue

                m = re.match(r'([_A-Z0-9a-z]+)(.py)?', name)
                if not m:
                    continue

                if load_plugin(f'{module_prefix}.{m.group(1)}'):
                    count += 1
    count = 0
    fors(plugin_dir, module_prefix)
    fors(os.path.join(os.path.dirname(__file__), 'plugins'), 'miraibot.plugins')
    LoggingLogger.info(f'共导入了 {count} 个插件')
    return count


def load_builtin_plugins() -> int:
    """
    加载与 "miraibot" 软件包一起分发的内置插件。
    """
    plugin_dir = os.path.join(os.path.dirname(__file__), 'plugins')
    return load_plugins(plugin_dir, 'miraibot.plugins')


def get_loaded_plugins() -> object:
    """
    加载所有插件。

    :return: 一组插件对象
    """
    return _plugins
