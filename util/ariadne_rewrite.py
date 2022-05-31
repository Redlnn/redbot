#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING

from graia.ariadne.model import LogConfig
from graia.ariadne.util import gen_subclass

if TYPE_CHECKING:
    from graia.ariadne.event import MiraiEvent


class CustomLogConfig(LogConfig):
    def __init__(self, log_level: str = "INFO", logChat: bool = True):
        self.log_level: str = log_level

        if not logChat:
            return
        from graia.ariadne.event.message import (
            ActiveMessage,
            FriendMessage,
            GroupMessage,
            OtherClientMessage,
            StrangerMessage,
            TempMessage,
        )

        account_seg = "{ariadne.account}"
        msg_chain_seg = "{event.messageChain.safe_display}"
        sender_seg = "{event.sender.name}({event.sender.id})"
        user_seg = "{event.sender.nickname}({event.sender.id})"
        group_seg = "{event.sender.group.name}({event.sender.group.id})"
        client_seg = "{event.sender.platform}({event.sender.id})"
        self[GroupMessage] = f"{account_seg}: [{group_seg}] {sender_seg} -> {msg_chain_seg}"
        self[TempMessage] = f"{account_seg}: [{group_seg}.{sender_seg}] -> {msg_chain_seg}"
        self[FriendMessage] = f"{account_seg}: [{user_seg}] -> {msg_chain_seg}"
        self[StrangerMessage] = f"{account_seg}: [{user_seg}] -> {msg_chain_seg}"
        self[OtherClientMessage] = f"{account_seg}: [{client_seg}] -> {msg_chain_seg}"
        for active_msg_cls in gen_subclass(ActiveMessage):
            sync_label: str = "[SYNC] " if active_msg_cls.__fields__["sync"].default else ""
            self[active_msg_cls] = f"{account_seg}: {sync_label}[{{event.subject}}] <- {msg_chain_seg}"
