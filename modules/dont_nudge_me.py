#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import contextlib
import os
from pathlib import Path
from posixpath import basename
from random import choice, randrange, uniform

from graia.ariadne.app import Ariadne
from graia.ariadne.event.mirai import NudgeEvent
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema

from util.config import basic_cfg
from util.control import DisableModule
from util.control.interval import ManualInterval
from util.path import data_path

channel = Channel.current()

channel.meta['name'] = '别戳我'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = '戳一戳bot'

msg = (
    '别{}啦别{}啦，无论你再怎么{}，我也不会多说一句话的~',
    '你再{}！你再{}！你再{}试试！！',
    '那...那里...那里不能{}...绝对...绝对不能（小声）...',
    '那里不可以...',
    '怎么了怎么了？发生什么了？！纳尼？没事？没事你{}我干哈？',
    '气死我了！别{}了别{}了！再{}就坏了呜呜...┭┮﹏┭┮',
    '呜…别{}了…',
    '呜呜…受不了了',
    '别{}了！...把手拿开呜呜..',
    'hentai！八嘎！无路赛！',
    '変態！バカ！うるさい！',
    '。',
    '哼哼╯^╰',
)


async def get_message(event: NudgeEvent):
    tmp = randrange(0, len(os.listdir(Path(data_path, 'Nudge'))) + len(msg))
    if tmp < len(msg):
        return MessageChain.create(Plain(msg[tmp].replace('{}', event.msg_action[0])))
    if not Path(data_path, 'Nudge').exists():
        Path(data_path, 'Nudge').mkdir()
    elif len(os.listdir(Path(data_path, 'Nudge'))) == 0:
        return MessageChain.create(Plain(choice(msg).replace('{}', event.msg_action[0])))
    return MessageChain.create(
        Image(path=Path(data_path, 'Nudge', os.listdir(Path(data_path, 'Nudge'))[tmp - len(msg)]))
    )


@channel.use(ListenerSchema(listening_events=[NudgeEvent], decorators=[DisableModule.require(channel.module)]))
async def main(app: Ariadne, event: NudgeEvent):
    if event.target != basic_cfg.miraiApiHttp.account:
        return
    elif not ManualInterval.require(f'{event.supplicant}_{event.group_id if event.friend_id is not None else None}', 3):
        return
    await asyncio.sleep(uniform(0.2, 0.6))
    with contextlib.suppress(UnknownTarget):
        await app.sendNudge(event.supplicant, event.group_id)  # 当戳一戳来自好友时 event.group_id 为 None，因此这里不判断也可以
        await asyncio.sleep(uniform(0.2, 0.6))
        if event.context_type == "friend" and event.friend_id:
            await app.sendFriendMessage(event.friend_id, (await get_message(event)))
        elif event.context_type == "group" and event.group_id:
            await app.sendGroupMessage(event.group_id, (await get_message(event)))
