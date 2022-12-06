import traceback
from io import StringIO

from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graiax.shortcut.saya import listen
from graia.broadcast.builtin.event import ExceptionThrowed
from graia.saya import Channel

from util.config import basic_cfg
from util.text2img import md2img

channel = Channel.current()
channel.meta['can_disable'] = False


@listen(ExceptionThrowed)
async def except_handle(event: ExceptionThrowed):
    if isinstance(event.event, ExceptionThrowed):
        return
    app = Ariadne.current()
    with StringIO() as fp:
        traceback.print_tb(event.exception.__traceback__, file=fp)
        tb = fp.getvalue()
    msg = f'''\
## 异常事件：

{str(event.event.__repr__())}

## 异常类型：

`{type(event.exception)}`

## 异常内容：

{str(event.exception)}

## 异常追踪：

```py
{tb}
```
'''
    img_bytes = await md2img(msg, 1500)
    await app.send_friend_message(basic_cfg.admin.masterId, MessageChain(Plain('发生异常\n'), Image(data_bytes=img_bytes)))


# from graia.ariadne.event.message import GroupMessage


# @listen(GroupMessage)
# async def error_handler_test(msg: MessageChain):
#     if str(msg) == '.错误捕捉测试':
#         raise ValueError('错误捕捉测试')
