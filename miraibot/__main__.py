#!/usr/bin/env python3

from os import path, chdir, getcwd

import config
import miraibot


if __name__ == "__main__":
    miraibot.init(config)
    miraibot.load_plugins(
        path.join(getcwd(), 'plugins'),
        'plugins'
    )
    miraibot.run()
