#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, AtAll, Image, Plain, Source
from graia.ariadne.message.parser.twilight import RegexMatch, Twilight
from graia.ariadne.model import Group, Member
from graia.ariadne.util.interrupt import FunctionWaiter
from graia.ariadne.util.saya import decorate, dispatch, listen
from graia.saya import Channel

from util import GetAiohttpSession
from util.control import require_disable
from util.control.interval import GroupInterval
from util.control.permission import GroupPermission
from util.text2img import async_generate_img

channel = Channel.current()

channel.meta['name'] = '消息转图片'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = '仿锤子便签样式的消息转图片，支持纯文本与图像\n用法：\n  [!！.](文本转图片|消息转图片)'


@listen(GroupMessage)
@dispatch(Twilight(RegexMatch(r'[!！.](文本转图片|消息转图片)')))
@decorate(GroupPermission.require(), GroupInterval.require(15), require_disable(channel.module))
async def main(app: Ariadne, group: Group, member: Member, source: Source):
    await app.send_message(group, MessageChain(Plain('请发送要转换的内容')), quote=source)

    async def waiter(waiter_group: Group, waiter_member: Member, waiter_message: MessageChain) -> MessageChain | None:
        if waiter_group.id == group.id and waiter_member.id == member.id:
            return waiter_message.include(Plain, At, Image)

    answer = await FunctionWaiter(waiter, [GroupMessage]).wait(timeout=10)
    if answer is None:
        await app.send_message(group, MessageChain(Plain('已超时取消')), quote=source)
        return

    if len(answer) == 0:
        await app.send_message(group, MessageChain(Plain('你所发送的消息的类型错误')), quote=source)
        return

    img_list: list[str | bytes] = []
    session = GetAiohttpSession.get_session()
    for ind, elem in enumerate(answer[:]):
        if type(elem) in {At, AtAll}:
            answer.__root__[ind] = Plain(str(elem))
    for i in answer[:]:
        if isinstance(i, Image) and i.url:
            async with session.get(i.url) as resp:
                img_list.append(await resp.content.read())
        else:
            img_list.append(str(i))

    if img_list:
        img_bytes = await async_generate_img(img_list)
        await app.send_message(group, MessageChain(Image(data_bytes=img_bytes)))
