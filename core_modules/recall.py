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
from graia.ariadne.message.element import Plain, Source
from graia.ariadne.model import Group
from graia.saya import Channel
from graia.scheduler.saya import SchedulerSchema
from graia.scheduler.timers import crontabify
from graiax.shortcut.saya import decorate, listen

from libs.config import basic_cfg
from libs.control import require_disable

channel = Channel.current()

channel.meta['name'] = '撤回自己的消息'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = '撤回bot发的消息\n用法：\n  回复bot的某条消息【撤回】，或发送【撤回最近】以撤回最近发送的消息'
channel.meta['can_disable'] = False


@listen(GroupMessage)
@decorate(require_disable(channel.module))
async def recall_message(app: Ariadne, group: Group, message: MessageChain, event: GroupMessage, memcache: Memcache):
    if event.sender.id not in basic_cfg.admin.admins:
        return
    if str(message) == '.撤回最近':
        recent_msg: list[dict] = await memcache.get('recent_msg', [])
        for item in recent_msg:
            with contextlib.suppress(UnknownTarget, InvalidArgument, RemoteException, UnknownError):
                await app.recall_message(item['id'])
            with contextlib.suppress(ValueError):
                recent_msg.remove(item)
                await memcache.set('recent_msg', recent_msg)
    elif event.quote is not None:
        if event.quote.sender_id != basic_cfg.miraiApiHttp.account:
            return
        if str(message.include(Plain).merge()).strip() == '.撤回':
            target_id = event.quote.id
            recent_msg: list[dict] = await memcache.get('recent_msg', [])
            for item in recent_msg:
                if item['id'] == target_id:
                    if item['time'] - time.time() > 115:
                        await app.send_message(group, MessageChain(Plain('该消息已超过撤回时间。')), quote=event.source)

                        return
                    with contextlib.suppress(UnknownTarget, InvalidArgument, RemoteException, UnknownError):
                        await app.recall_message(item['id'])
                    with contextlib.suppress(ValueError):
                        recent_msg.remove(item)
                        await memcache.set('recent_msg', recent_msg)
                    break


@listen(ActiveGroupMessage)
@decorate(require_disable(channel.module))
async def listener(source: Source, memcache: Memcache):
    recent_msg: list[dict] = await memcache.get('recent_msg', [])
    recent_msg.append(
        {
            'time': datetime.timestamp(source.time),
            'id': source.id,
        }
    )
    await memcache.set('recent_msg', recent_msg)


@channel.use(SchedulerSchema(crontabify('0/2 * * * *')))
async def clear_outdated(app: Ariadne):
    time_now = time.time()
    memcache = app.launch_manager.get_interface(Memcache)
    recent_msg: list[dict] = await memcache.get('recent_msg', [])
    for item in recent_msg:
        if (time_now - item['time']) > 120:
            recent_msg.remove(item)
            await memcache.set('recent_msg', recent_msg)
