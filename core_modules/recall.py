#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from datetime import datetime
from os.path import basename

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import ActiveGroupMessage, GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Quote, Source
from graia.ariadne.model import Group, Member
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from graia.scheduler.saya import SchedulerSchema
from graia.scheduler.timers import crontabify

from util.config import basic_cfg
from util.control import DisableModule
from util.module_register import Module

channel = Channel.current()
module_name = basename(__file__)[:-3]

Module(
    name='撤回自己的消息',
    file_name=module_name,
    author=['Red_lnn'],
    description='撤回bot自己发的消息',
    usage='回复bot的某条消息【撤回】，或发送【撤回最近】以撤回最近发送的消息',
    can_disable=False,
).register()


lastest_msg: list[dict] = []


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        decorators=[DisableModule.require(module_name)],
    )
)
async def recall_message(app: Ariadne, group: Group, member: Member, message: MessageChain):
    if member.id not in basic_cfg.admin.admins:
        return
    if message.asDisplay() == '.撤回最近':
        for item in lastest_msg.copy():
            try:
                await app.recallMessage(item['id'])
            except:
                pass
            try:
                lastest_msg.remove(item)
            except ValueError:
                pass
    elif message.has(Quote):
        if message.getFirst(Quote).senderId != basic_cfg.miraiApiHttp.account:
            return
        print(f'"{message.include(Plain).merge().asDisplay().strip()}"')
        if message.include(Plain).merge().asDisplay().strip() == '.撤回':
            target_id = message.getFirst(Quote).id
            for item in lastest_msg.copy():
                if item['id'] == target_id:
                    if item['time'] - time.time() > 115:
                        await app.sendMessage(group, MessageChain.create(Plain(f'该消息已超过撤回时间。')), quote=True)
                        return
                    try:
                        await app.recallMessage(item['id'])
                    except:
                        pass
                    try:
                        lastest_msg.remove(item)
                    except ValueError:
                        pass
                    break


@channel.use(
    ListenerSchema(
        listening_events=[ActiveGroupMessage],
        decorators=[DisableModule.require(module_name)],
    )
)
async def listener(event: ActiveGroupMessage):
    source = event.messageChain.getFirst(Source)
    lastest_msg.append(
        {
            'time': datetime.timestamp(source.time),
            'id': source.id,
        }
    )


@channel.use(SchedulerSchema(crontabify('0 0/2 * * *')))
async def clear_outdated():
    time_now = time.time()
    for item in lastest_msg.copy():
        if (time_now - item['time']) > 120:
            lastest_msg.remove(item)
