from miraibot import GraiaMiraiApplication, get
from miraibot import schedule
from miraibot.message import Group, MessageChain, Plain, Member

bcc = get.bcc()

class data:
    def __init__(self):
        self.__data = None

    def set(self, d):
        self.__data = d

    def get(self):
        return self.__data

data = data()


async def job():
    import time
    data.set(time.strftime("%Y-%m-%d %a %H:%M:%S ", time.localtime()))


async def jobs(app, group):
    await app.sendGroupMessage(group, MessageChain.create([
        Plain(data.get())]))


@bcc.receiver("GroupMessage")
async def friend_message_listener(app: GraiaMiraiApplication, group: Group, member: Member, ctx: MessageChain):
    m = ctx.asDisplay()
    if m == '#time':
        if data.get() is None:
            msg = '暂未开启该功能'
        else:
            msg = data.get()
        await app.sendGroupMessage(group, MessageChain.create([
            Plain(msg)
        ]))
    elif m == '#开始':
        schedule.every(3).seconds.do(jobs, app=app, group=group).tag('daily-tasks', 'group')
        await app.sendGroupMessage(group, MessageChain.create([
            Plain('发送指令: #结束 以结束报时')
        ]))
    elif m == '#结束':
        schedule.clear('daily-tasks')
        await app.sendGroupMessage(group, MessageChain.create([
            Plain('已结束')
        ]))


def __init__():
    for i in range(60):
        if i < 10:
            schedule.every().minute.at(f":0{i}").do(job)
        else:
            schedule.every().minute.at(f":{i}").do(job)
    
    