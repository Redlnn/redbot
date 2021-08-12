#!/usr/bin/env python3

from os import path

import config
import miraibot


if __name__ == "__main__":
    miraibot.init(config)
    miraibot.load_plugins(
        path.join(path.dirname(__file__), 'plugins'),
        'plugins'
    )
    miraibot.run()
