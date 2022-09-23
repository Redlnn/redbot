#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import contextlib
import time
from datetime import datetime

from graia.amnesia.builtins.memcache import Memcache
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
from graia.ariadne.util.saya import decorate, listen
from graia.saya import Channel
from graia.scheduler.saya import SchedulerSchema
from graia.scheduler.timers import crontabify

from util.config import basic_cfg
from util.control import require_disable

channel = Channel.current()

channel.meta['name'] = '撤回自己的消息'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = '撤回bot发的消息\n用法：\n  回复bot的某条消息【撤回】，或发送【撤回最近】以撤回最近发送的消息'
channel.meta['can_disable'] = False


@listen(GroupMessage)
@decorate(require_disable(channel.module))
async def recall_message(app: Ariadne, group: Group, member: Member, message: MessageChain):
    if member.id not in basic_cfg.admin.admins:
        return
    if str(message) == '.撤回最近':
        recent_msg: list[dict] = await app.launch_manager.get_interface(Memcache).get('recent_msg', [])
        for item in recent_msg:
            with contextlib.suppress(UnknownTarget, InvalidArgument, RemoteException, UnknownError):
                await app.recall_message(item['id'])
            with contextlib.suppress(ValueError):
                recent_msg.remove(item)
                await app.launch_manager.get_interface(Memcache).set('recent_msg', recent_msg)
    elif message.has(Quote):
        if message.get_first(Quote).sender_id != basic_cfg.miraiApiHttp.account:
            return
        if str(message.include(Plain).merge()).strip() == '.撤回':
            target_id = message.get_first(Quote).id
            recent_msg: list[dict] = await app.launch_manager.get_interface(Memcache).get('recent_msg', [])
            for item in recent_msg:
                if item['id'] == target_id:
                    if item['time'] - time.time() > 115:
                        await app.send_message(group, MessageChain(Plain('该消息已超过撤回时间。')), quote=True)

                        return
                    with contextlib.suppress(UnknownTarget, InvalidArgument, RemoteException, UnknownError):
                        await app.recall_message(item['id'])
                    with contextlib.suppress(ValueError):
                        recent_msg.remove(item)
                        await app.launch_manager.get_interface(Memcache).set('recent_msg', recent_msg)
                    break


@listen(ActiveGroupMessage)
@decorate(require_disable(channel.module))
async def listener(app: Ariadne, event: ActiveGroupMessage):
    source = event.message_chain.get_first(Source)
    recent_msg: list[dict] = await app.launch_manager.get_interface(Memcache).get('recent_msg', [])
    recent_msg.append(
        {
            'time': datetime.timestamp(source.time),
            'id': source.id,
        }
    )
    await app.launch_manager.get_interface(Memcache).set('recent_msg', recent_msg)


@channel.use(SchedulerSchema(crontabify('0/2 * * * *')))
async def clear_outdated(app: Ariadne):
    time_now = time.time()
    recent_msg: list[dict] = await app.launch_manager.get_interface(Memcache).get('recent_msg', [])
    for item in recent_msg:
        if (time_now - item['time']) > 120:
            recent_msg.remove(item)
            await app.launch_manager.get_interface(Memcache).set('recent_msg', recent_msg)
