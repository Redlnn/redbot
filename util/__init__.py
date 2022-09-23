#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING

from aiohttp import ClientSession
from loguru import logger
from richuru import LoguruHandler, install

from util.config import basic_cfg
from util.path import logs_path

if TYPE_CHECKING:
    from graia.ariadne.event import MiraiEvent


def get_graia_version():

    extra: list[tuple[str, str]] = []
    official: list[tuple[str, str]] = []
    community: list[tuple[str, str]] = []

    for dist in metadata.distributions():
        name: str = dist.metadata['Name']
        version: str = dist.version
        if name in {'launart', 'creart', 'creart-graia', 'statv', 'richuru'}:
            extra.append((name, version))
        elif name.startswith('graia-'):
            official.append((name, version))
        elif name.startswith('graiax-'):
            community.append((name, version))

    return extra, official, community


def replace_logger(level: str | int = 'INFO', richuru: bool = False):
    if richuru:
        install(level=level)
    else:
        logging.basicConfig(handlers=[LoguruHandler()], level=0)
        logger.remove()
        logger.add(sys.stderr, level=level, enqueue=True)
    logger.add(
        Path(logs_path, 'latest.log'),
        level=level,
        rotation='00:00',
        retention='30 days',
        compression='zip',
        encoding='utf-8',
        enqueue=True,
    )


def log_level_handler(event: 'MiraiEvent'):
    if basic_cfg.debug:
        return 'DEBUG'
    from graia.ariadne.event.message import (
        ActiveMessage,
        FriendMessage,
        GroupMessage,
        OtherClientMessage,
        StrangerMessage,
        TempMessage,
    )

    if type(event) in {
        ActiveMessage,
        FriendMessage,
        GroupMessage,
        OtherClientMessage,
        StrangerMessage,
        TempMessage,
    }:
        return 'INFO' if basic_cfg.logChat else 'DEBUG'
    return 'INFO'
