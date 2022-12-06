import re

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Quote
from graia.ariadne.model import Group, MemberPerm
from graiax.shortcut.saya import decorate, listen
from graia.saya import Channel

from util.control import require_disable
from util.control.permission import GroupPermission

channel = Channel.current()

channel.meta['name'] = '读取/发送消息的可持久化字符串'
channel.meta['author'] = ['Red_lnn']
# fmt: off
channel.meta['description'] = (
    '仅限群管理员使用\n'
    ' - 回复需要读取的消息并且回复内容只含有“[!！.]读取消息”获得消息的可持久化字符串\n'
    ' - [!！.]发送消息 <可持久化字符串> —— 用于从可持久化字符串发送消息'
)
# fmt: on


@listen(GroupMessage)
@decorate(GroupPermission.require(MemberPerm.Administrator, send_alert=False), require_disable(channel.module))
async def main(app: Ariadne, group: Group, message: MessageChain, quote: Quote):
    if re.match(r'^[!！.]读取消息$', str(message)):
        try:
            message_event = await app.get_message_from_id(quote.id)
        except UnknownTarget:
            await app.send_message(group, MessageChain(Plain('找不到该消息，对象不存在')))
            return
        chain = message_event.message_chain
        await app.send_message(group, MessageChain(Plain(f'消息ID: {quote.id}\n消息内容：{chain.as_persistent_string()}')))
    elif re.match(r'^[!！.]发送消息 .+', str(message)):
        if msg := re.sub(r'[!！.]发送消息 ', '', str(message), count=1):
            await app.send_message(group, MessageChain.from_persistent_string(msg))
