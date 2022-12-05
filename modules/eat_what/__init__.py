import random
from pathlib import Path

from aiofile import async_open
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Source
from graia.ariadne.message.parser.twilight import RegexMatch, SpacePolicy, Twilight
from graia.ariadne.model import Group
from graia.ariadne.util.saya import decorate, dispatch, listen
from graia.saya import Channel

from util.control import require_disable
from util.control.permission import GroupPermission

channel = Channel.current()

channel.meta['name'] = '吃啥'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = '[!！.]吃啥'


async def get_food():
    async with async_open(Path(Path(__file__).parent, 'foods.txt')) as afp:
        foods = await afp.read()
    return random.choice(foods.strip().split('\n'))


@listen(GroupMessage)
@dispatch(Twilight(RegexMatch(r'[!！.]吃啥').space(SpacePolicy.NOSPACE)))
@decorate(GroupPermission.require(), require_disable(channel.module))
async def main(app: Ariadne, group: Group, source: Source):
    food = await get_food()
    chain = MessageChain(Plain(f'吃{food}'))
    await app.send_message(group, chain, quote=source)
