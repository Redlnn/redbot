#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import TypeVar, overload

from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain
from graia.ariadne.model import BotMessage
from graia.ariadne.typing import SendMessageAction, SendMessageException
from graia.ariadne.util.send import Ignore

Exc_T = TypeVar('Exc_T', bound=SendMessageException)


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
    async def exception(item) -> BotMessage:
        ...

    @overload
    async def exception(self, item) -> BotMessage:
        ...

    @staticmethod
    async def _handle(item: SendMessageException, ignore: bool):
        chain: MessageChain = item.send_data['message']
        ariadne = Ariadne.current()

        def convert(msg_chain: MessageChain, type_: str) -> None:
            for ind, elem in enumerate(msg_chain.__root__[:]):
                if elem.type == type_:
                    if elem.type == 'at':
                        msg_chain.__root__[ind] = (
                            Plain(f'@{elem.display}({elem.target})')  # type: ignore
                            if elem.display is not None
                            else Plain(f'@{elem.target}')  # type: ignore
                        )
                    else:
                        msg_chain.__root__[ind] = Plain(elem.display)

        for element_type in {'AtAll', 'At', 'Poke', 'Forward', 'MultimediaElement'}:
            convert(chain, element_type)
            val = await ariadne.send_message(**item.send_data, action=Ignore)  # type: ignore # noqa
            if val is not None:
                return val

        if not ignore:
            raise item

    @overload
    @staticmethod
    async def exception(s, i):
        ...

    @overload
    async def exception(self, i):
        ...

    async def exception(self: 'Safe' | Exc_T, i: Exc_T | None = None):  # type: ignore # noqa
        if not isinstance(self, Safe):
            return await Safe._handle(self, True)
        if i:
            return await Safe._handle(i, self.ignore)
