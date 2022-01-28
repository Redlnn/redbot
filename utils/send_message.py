#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

from graia.ariadne.context import ariadne_ctx
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain, Source
from graia.ariadne.model import BotMessage, Group


async def safeSendGroupMessage(
    target: Group | int,
    message: MessageChain,
    *,
    quote: Optional[Source | int] = None,
) -> BotMessage:
    app = ariadne_ctx.get()
    try:
        return await app.sendGroupMessage(target, message, quote=quote)
    except UnknownTarget:
        msg = []
        for element in message.__root__:
            if isinstance(element, At):
                member = await app.getMember(target, element.target)
                if member:
                    at_target = f'{member.name}({member.id})'
                else:
                    at_target = str(element.target)
                msg.append(Plain(at_target))
                continue
            msg.append(element)
        try:
            return await app.sendGroupMessage(target, MessageChain.create(msg), quote=quote)
        except UnknownTarget:
            return await app.sendGroupMessage(target, MessageChain.create(msg))
