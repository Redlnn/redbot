from miraibot import GraiaMiraiApplication, get
from miraibot.message import Group, MessageChain, Plain, Quote,Source
from config import QQ

import re
from urllib import parse

bcc = get.bcc()


@bcc.receiver("GroupMessage")
async def friend_message_listener(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    m = message.asDisplay()
    if m.endswith("帮楼上百度"):
        if message.has(Quote):
            quote: Quote = message.get(Quote).pop(0)
            source = message.get(Source).pop(0)
            if quote.senderId != QQ:
                ctx = MessageChain.create(quote.origin.get(Plain)).asDisplay()
                while ctx.startswith(" "):
                    ctx = ctx[1:]
                await app.sendGroupMessage(group, MessageChain.create([Plain("请在这里找答案哦:\n"), Plain("https://www.baidu.com/s?wd="), Plain(parse.quote(ctx))]), quote=source)
            else:
                await app.sendGroupMessage(group, MessageChain.create([Plain("竹竹知道自己说的是什么东西啦~")]))
