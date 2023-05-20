import asyncio
import contextlib
import os
from pathlib import Path
from random import choice, randrange, uniform

from graia.ariadne.app import Ariadne
from graia.ariadne.event.mirai import NudgeEvent
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.model import Friend, Group
from graia.saya import Channel
from graiax.shortcut.saya import decorate, listen

from util.config import basic_cfg
from util.control import require_disable
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
        return MessageChain(Plain(msg[tmp].replace('{}', event.msg_action[0])))
    if not Path(data_path, 'Nudge').exists():
        Path(data_path, 'Nudge').mkdir()
    elif len(os.listdir(Path(data_path, 'Nudge'))) == 0:
        return MessageChain(Plain(choice(msg).replace('{}', event.msg_action[0])))
    return MessageChain(Image(path=Path(data_path, 'Nudge', os.listdir(Path(data_path, 'Nudge'))[tmp - len(msg)])))


@listen(NudgeEvent)
@decorate(require_disable(channel.module))
async def main(app: Ariadne, event: NudgeEvent):
    if event.target != basic_cfg.miraiApiHttp.account:
        return
    elif not ManualInterval.require(f'{event.supplicant}_{event.target}', 3):
        return
    await asyncio.sleep(uniform(0.2, 0.6))
    with contextlib.suppress(UnknownTarget):
        await app.send_nudge(event.supplicant, event.target)
        await asyncio.sleep(uniform(0.2, 0.6))
        if isinstance(event.subject, Group | Friend):
            await app.send_message(event.subject, (await get_message(event)))
