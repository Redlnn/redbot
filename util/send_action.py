#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, TypeVar, Union, overload

from graia.ariadne.model import BotMessage
from graia.ariadne.typing import SendMessageAction, SendMessageException
from graia.ariadne.util.send import Ignore

Exc_T = TypeVar("Exc_T", bound=SendMessageException)


class Safe(SendMessageAction):
    """
    安全发送的 SendMessage action

    行为:
    在第一次尝试失败后先移除 quote,
    之后每次失败时按顺序替换元素为其asDisplay: AtAll, At, Poke, Forward, MultimediaElement
    若最后还是失败 (AccountMuted 等), 则会引发原始异常 (通过传入 ignore 决定)
    """

    def __init__(self, ignore: bool = False) -> None:
        self.ignore: bool = ignore

    @overload
    @staticmethod
    async def exception(item: Exc_T, /) -> BotMessage:
        ...

    @overload
    async def exception(self, item: Exc_T, /) -> BotMessage:
        ...

    @staticmethod
    async def _handle(item: Exc_T, ignore: bool):
        from graia.ariadne.context import ariadne_ctx
        from graia.ariadne.message.chain import MessageChain
        from graia.ariadne.message.element import (
            At,
            AtAll,
            Forward,
            MultimediaElement,
            Plain,
            Poke,
        )

        chain: MessageChain = item.send_data["message"]
        ariadne = ariadne_ctx.get()

        def convert(msg_chain: MessageChain, type_) -> None:
            for ind, elem in enumerate(msg_chain.__root__[:]):
                if isinstance(elem, type_):
                    if isinstance(elem, At):
                        msg_chain.__root__[ind] = (
                            Plain(f'@{elem.display}({elem.target})') if elem.display else Plain(elem.asDisplay())
                        )
                    else:
                        msg_chain.__root__[ind] = Plain(elem.asDisplay())

        for element_type in [AtAll, At, Poke, Forward, MultimediaElement]:
            convert(chain, element_type)
            val = await ariadne.sendMessage(**item.send_data, action=Ignore)  # noqa
            if val is not None:
                return val

        if not ignore:
            raise item

    async def exception(s: Union["Safe", Exc_T], i: Optional[Exc_T] = None):  # noqa
        if isinstance(s, Safe):
            return await Safe._handle(i, s.ignore)
        return await Safe._handle(s, True)
