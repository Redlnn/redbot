from miraibot import GraiaMiraiApplication, get
from miraibot.message import Group, MessageChain, Plain
from config import QQ

import re
from urllib import parse

bcc = get.bcc()


@bcc.receiver("GroupMessage")
async def friend_message_listener(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    m = message.asDisplay()
    if m.endswith('帮楼上百度'):
        if message.__root__[1].senderId != QQ:
            red = re.search(r'^\[\[.+?]]', m)
            if red is not None:
                red = re.search(r'(?<=text=).+?(?=]])', red.group())
                if red is not None:
                    data = await app.sendGroupMessage(
                        group,
                        MessageChain.create(
                            [
                                Plain(f'请在这里找答案哦:\nhttps://www.baidu.com/s?wd={parse.quote(f"{red.group()}")}')
                            ]),
                        quote=message.__root__[1].origin.__root__[0]
                    )
                    if data['code'] != 0:
                        await app.sendGroupMessage(
                            group,
                            MessageChain.create(
                                [
                                    Plain('竹竹没能在手机上找到这条消息呢~')
                                ]
                            )
                        )
        else:
            await app.sendGroupMessage(
                group,
                MessageChain.create(
                    [
                        Plain('竹竹知道自己说的是什么东西的啦~')
                    ]
                )

            )
