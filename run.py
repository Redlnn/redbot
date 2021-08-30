#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import path

import config
import miraibot

if __name__ == "__main__":
    miraibot.init(config)
    miraibot.logger.info('加载内置插件中...')
    miraibot.load_builtin_plugins()
    miraibot.logger.info('加载外部插件中...')
    miraibot.load_plugins(
        path.join(path.dirname(__file__), 'plugins'), 'plugins'
    )
    miraibot.run()
