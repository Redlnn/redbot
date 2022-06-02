#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from importlib import metadata
from typing import TYPE_CHECKING

from aiohttp import ClientSession

from util.config import basic_cfg

if TYPE_CHECKING:
    from graia.ariadne.event import MiraiEvent


def get_graia_version():

    official: list[tuple[str, str]] = []
    community: list[tuple[str, str]] = []

    for dist in metadata.distributions():
        name: str = dist.metadata['Name']
        version: str = dist.version
        if name.startswith('graia-'):
            official.append((' '.join(name.split('-')[1:]).title(), version))
        elif name.startswith('graiax-'):
            community.append((' '.join(name.split('-')).title(), version))

    return official, community


class GetAiohttpSession:
    session: ClientSession | None = None

    @classmethod
    def get_session(cls) -> ClientSession:
        if cls.session is None:
            cls.session = ClientSession()
        return cls.session


def log_level_handler(event: 'MiraiEvent'):
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
        return 'DEBUG' if basic_cfg.debug or not basic_cfg.logChat else 'INFO'
    return 'INFO'
