#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import contextlib
import time
from contextvars import ContextVar
from datetime import datetime

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import ActiveGroupMessage, GroupMessage
from graia.ariadne.exception import (
    InvalidArgument,
    RemoteException,
    UnknownError,
    UnknownTarget,
)
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Quote, Source
from graia.ariadne.model import Group, Member
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from graia.scheduler.saya import SchedulerSchema
from graia.scheduler.timers import crontabify

from util.config import basic_cfg
from util.control import require_disable

channel = Channel.current()

channel.meta['name'] = '撤回自己的消息'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = '撤回bot发的消息\n用法：\n  回复bot的某条消息【撤回】，或发送【撤回最近】以撤回最近发送的消息'
channel.meta['can_disable'] = False

lastest_msg: ContextVar[list[dict]] = ContextVar('lastest_msg', default=[])


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        decorators=[require_disable(channel.module)],
    )
)
async def recall_message(app: Ariadne, group: Group, member: Member, message: MessageChain):
    if member.id not in basic_cfg.admin.admins:
        return
    if message.asDisplay() == '.撤回最近':
        msg_list = lastest_msg.get()
        for item in msg_list:
            with contextlib.suppress(UnknownError, UnknownTarget):
                await app.recallMessage(item['id'])
            with contextlib.suppress(ValueError):
                msg_list.remove(item)
                lastest_msg.set(msg_list)
    elif message.has(Quote):
        if message.getFirst(Quote).senderId != basic_cfg.miraiApiHttp.account:
            return
        print(f'"{message.include(Plain).merge().asDisplay().strip()}"')
        if message.include(Plain).merge().asDisplay().strip() == '.撤回':
            target_id = message.getFirst(Quote).id
            msg_list = lastest_msg.get()
            for item in msg_list:
                if item['id'] == target_id:
                    if item['time'] - time.time() > 115:
                        await app.sendMessage(
                            group,
                            MessageChain.create(Plain('该消息已超过撤回时间。')),
                            quote=True,
                        )

                        return
                    with contextlib.suppress(UnknownTarget, InvalidArgument, RemoteException, UnknownError):
                        await app.recallMessage(item['id'])
                    with contextlib.suppress(ValueError):
                        msg_list.remove(item)
                        lastest_msg.set(msg_list)
                    break


@channel.use(
    ListenerSchema(
        listening_events=[ActiveGroupMessage],
        decorators=[require_disable(channel.module)],
    )
)
async def listener(event: ActiveGroupMessage):
    source = event.messageChain.getFirst(Source)
    msg_list = lastest_msg.get()
    msg_list.append(
        {
            'time': datetime.timestamp(source.time),
            'id': source.id,
        }
    )
    lastest_msg.set(msg_list)


@channel.use(SchedulerSchema(crontabify('0/2 * * * *')))
async def clear_outdated():
    time_now = time.time()
    msg_list = lastest_msg.get()
    for item in msg_list:
        if (time_now - item['time']) > 120:
            msg_list.remove(item)
            lastest_msg.set(msg_list)
