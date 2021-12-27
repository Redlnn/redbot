#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
人品测试

每个QQ号每天可随机获得一个0-100的整数（人品值），在当天内该值不会改变，该值会存放于一yml文件中，每日删除过期文件

用法：[!！.#](jrrp|抽签) （jrrp 即 JinRiRenPin）
"""

import datetime
import os
import random
from os.path import basename
from pathlib import Path
from typing import Tuple

import orjson as json
import regex as re
from graia.ariadne.app import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Plain
from graia.ariadne.message.parser.twilight import RegexMatch, Sparkle, Twilight
from graia.ariadne.model import Group, Member
from graia.ariadne.util.async_exec import io_bound
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from graia.scheduler.saya import SchedulerSchema
from graia.scheduler.timers import crontabify
from loguru import logger

from utils.config import get_modules_config
from utils.control.interval import MemberInterval
from utils.control.permission import GroupPermission
from utils.module_register import Module
from utils.path import data_path
from utils.text2img import async_generate_img, hr

channel = Channel.current()
modules_cfg = get_modules_config()
module_name = basename(__file__)

Module(
    name='人品测试',
    file_name=module_name,
    author=['Red_lnn'],
    description='每个QQ号每天可抽一次签并获得人品值',
    usage='[!！.]jrrp / [!！.]抽签',
).register()

# https://wiki.biligame.com/ys/%E3%80%8C%E5%BE%A1%E7%A5%9E%E7%AD%BE%E3%80%8D
qianwens = {
    '大吉': [
        '会起风的日子，无论干什么都会很顺利的一天。\n'
        '周围的人心情也非常愉快，绝对不会发生冲突，\n还可以吃到一直想吃，但没机会吃的美味佳肴。\n无论是工作，还是旅行，都一定会十分顺利吧。\n那么，应当在这样的好时辰里，一鼓作气前进…',
        '宝剑出匣来，无往不利。出匣之光，亦能照亮他人。\n今日能一箭射中空中的幻翼，能一击命中敌人的胸膛。\n若没有目标，不妨四处转转，说不定会有意外之喜。\n同时，也不要忘记和倒霉的同伴分享一下好运气哦。',
        '失而复得的一天。\n原本以为石沉大海的事情有了好的回应，\n原本分道扬镳的朋友或许可以再度和好，\n不经意间想起了原本已经忘记了的事情。\n世界上没有什么是永远无法挽回的，\n今天就是能够挽回失去事物的日子。',
        '浮云散尽月当空，逢此签者皆为上吉。\n明镜在心清如许，所求之事心想则成。\n合适顺心而为的一天，不管是想做的事情，\n还是想见的人，现在是行动起来的好时机。',
    ],
    '吉': [
        '浮云散尽月当空，逢此签者皆为上吉。\n明镜在心清如许，所求之事心想则成。\n合适顺心而为的一天，不管是想做的事情，\n还是想见的人，现在是行动起来的好时机。',
        '十年磨一剑，今朝示霜刃。恶运已销，身临否极泰来之时。苦练多年未能一显身手的才能，现今有了大展身手的极好机会。若是遇到阻碍之事，亦不必迷惘，大胆地拔剑，痛快地战斗一番吧。',
        '枯木逢春，正当万物复苏之时。\n陷入困境时，能得到解决办法。\n举棋不定时，会有贵人来相助。\n可以整顿一番心情，清理一番家装，\n说不定能发现意外之财。',
        '明明没有什么特别的事情，却感到心情轻快的日子。\n在没注意过的角落可以找到本以为丢失已久的东西。\n食物比平时更加鲜美，路上的风景也令人眼前一亮。\n——这个世界上充满了新奇的美好事物——',
        '一如既往的一天。身体和心灵都适应了的日常。\n出现了能替代弄丢的东西的物品，令人很舒心。\n和常常遇见的人关系会变好，可能会成为朋友。\n——无论是多寻常的日子，都能成为宝贵的回忆——',
    ],
    '末吉': [
        '云遮月半边，雾起更迷离\n抬头即是浮云遮月，低头则是浓雾漫漫\n虽然一时前路迷惘，但也会有一切明了的时刻\n现下不如趁此机会磨炼自我，等待拨云见皎月。',
        '空中的云层偏低，并且仍有堆积之势，\n不知何时雷雨会骤然从头顶倾盆而下。\n但是等雷雨过后，还会有彩虹在等着。\n宜循于旧，守于静，若妄为则难成之。',
        '平稳安详的一天。没有什么令人难过的事情会发生。\n适合和久未联系的朋友聊聊过去的事情，一同欢笑。\n吃东西的时候会尝到很久以前体验过的过去的味道。\n——要珍惜身边的人与事——',
        '气压稍微有点低，是会令人想到遥远的过去的日子。\n早已过往的年轻岁月，与再没联系过的故友的回忆，\n会让人感到一丝平淡的怀念，又稍微有一点点感伤。\n——偶尔怀念过去也很好。放松心情面对未来吧——',
    ],
    '凶': [
        '珍惜的东西可能会遗失，需要小心。\n如果身体有不适，一定要注意休息。\n在做出决定之前，一定要再三思考。',
        '内心空落落的一天。可能会陷入深深的无力感之中。\n很多事情都无法理清头绪，过于钻牛角尖则易生病。\n虽然一切皆陷于低潮谷底中，但也不必因此而气馁。\n若能撑过一时困境，他日必另有一番作为。',
        '隐约感觉会下雨的一天。可能会遇到不顺心的事情。\n应该的褒奖迟迟没有到来，服务生也可能会上错菜。\n明明没什么大不了的事，却总感觉有些心烦的日子。\n——难免有这样的日子——',
    ],
}

lucky_things = {
    '吉': [
        '散发暖意的「鸡蛋」。\n鸡蛋孕育着无限的可能性，是未来之种。\n反过来，这个世界对鸡蛋中的生命而言，\n也充满了令其兴奋的未知事物吧。\n要温柔对待鸡蛋喔。',
        '节节高升的「竹笋」。\n竹笋拥有着无限的潜力，\n没有人知道一颗竹笋，到底能长成多高的竹子。\n看着竹笋，会让人不由自主期待起未来吧。',
        '闪闪发亮的「下界之星」。\n下届之星可以做成直上云霄的信标。\n而信标是这个世界最令人憧憬的事物之一吧，他能许以天地当中人们的祝福。',
        '色泽艳丽的「金萝卜」。\n人们常说表里如一是美德，\n但金萝卜明艳的外貌下隐藏着的是谦卑而甘甜的内在。',
        '生长多年的「钟乳石」。\n脆弱的滴水石锥在无人而幽黑的洞穴中历经多年的寂寞，才能结成钟乳石。\n为目标而努力前行的人们，最终也必将拥有胜利的果实。',
        '难得一见的「附魔金苹果」。\n附魔金苹果非常地难寻，他藏匿于废弃遗迹的杂物中，\n与傲然挺立于此世的你一定很是相配。',
        '活蹦乱跳的「兔兔」。\n兔兔是爱好和平、不愿意争斗的小生物。\n这份追求平和的心一定能为你带来幸福吧。',
        '不断发热的「烈焰棒」。\n烈焰棒的炙热来自于烈焰人那火辣辣的心。\n万事顺利是因为心中自有一条明路。',
    ],
    '凶': [
        '暗中发亮的「发光地衣」。\n发光地衣努力地发出微弱的光芒。\n虽然比不过其他光源，但看清前路也够用了。',
        '树上掉落的「树苗」。\n并不是所有的树苗都能长成粗壮的大树，\n成长需要适宜的环境，更需要一点运气。\n所以不用给自己过多压力，耐心等待彩虹吧。',
        '黯淡无光的「火药」。\n火药蕴含着无限的能量。\n如果能够好好导引这股能量，说不定就能成就什么事业。',
        '随风飞翔的「蒲公英」。\n只要有草木生长的空间，就一定有蒲公英。\n这么看来，蒲公英是世界上最强韧的生灵。\n据说连坑坑洼洼的沼泽也能长出蒲公英呢。',
        '冰凉冰凉的「蓝冰」。\n冰山上的蓝冰散发着「生人勿进」的寒气。\n但有时冰冷的气质，也能让人的心情与头脑冷静下来。\n据此采取正确的判断，明智地行动。',
        '随波摇曳的「海草」。\n海草是相当温柔而坚强的植物，\n即使在苦涩的海水中，也不愿改变自己。\n即使在逆境中，也不要放弃温柔的心灵。',
        '半丝半缕的「线」。\n有一些线特别细，细得轻轻一碰就会断开。\n若是遇到无法整理的情绪，那么该断则断吧。',
    ],
}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'[!！.](jrrp|抽签)')]))],
        decorators=[GroupPermission.require(), MemberInterval.require(10)],
    )
)
async def main(app: Ariadne, group: Group, member: Member):
    if module_name in modules_cfg.disabledGroups:
        if group.id in modules_cfg.disabledGroups[module_name]:
            return
    is_new, renpin, qianwen = await read_data(str(member.id))
    img_bytes = await async_generate_img([qianwen, f'\n{hr}\n悄悄告诉你噢，你今天的人品值是 {renpin}'])
    if is_new:
        await app.sendGroupMessage(
            group, MessageChain.create(At(member.id), Plain(' 你抽到一支签：'), Image(data_bytes=img_bytes))
        )
    else:
        await app.sendGroupMessage(
            group,
            MessageChain.create(
                At(member.id), Plain(' 你今天已经抽到过一支签了，你没有好好保管吗？这样吧，再告诉你一次好了，你抽到的签是：'), Image(data_bytes=img_bytes)
            ),
        )


@channel.use(SchedulerSchema(crontabify('0 0 * * *')))
async def scheduled_del_outdated_data() -> None:
    """
    定时删除过时的数据文件
    """
    for _ in os.listdir(data_path):
        if (
            re.match('jrrp_20[0-9]{2}-[0-9]{2}-[0-9]{2}.yml', _)
            and _ != f'jrrp_{datetime.datetime.now().strftime("%Y-%m-%d")}.yml'
        ):
            os.remove(Path(data_path, _))
            logger.info(f'发现过期的数据文件 {_}，已删除')


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def del_outdated_data() -> None:
    """
    在bot启动时删除过时的数据文件
    """
    for _ in os.listdir(data_path):
        if (
            re.match('jrrp_20[0-9]{2}-[0-9]{2}-[0-9]{2}.json', _)
            and _ != f'jrrp_{datetime.datetime.now().strftime("%Y-%m-%d")}.json'
        ):
            os.remove(Path(data_path, _))
            logger.info(f'发现过期的数据文件 {_}，已删除')


def chouqian(renpin: int) -> str:
    if renpin >= 90:
        return '大吉'
    elif renpin >= 75:
        return '中吉'
    elif renpin >= 55:
        return '吉'
    elif renpin >= 30:
        return '末吉'
    elif renpin >= 10:
        return '凶'
    else:
        return '大凶'


def gen_qianwen(renpin: int) -> str:
    match chouqian(renpin):
        case '大吉':
            return '——大吉——\n' f'{random.choice(qianwens["大吉"])}\n\n' f'今天的幸运物是：{random.choice(lucky_things["吉"])}'
        case '中吉':
            return '——中吉——\n' f'{random.choice(qianwens["吉"])}\n\n' f'今天的幸运物是：{random.choice(lucky_things["吉"])}'
        case '吉':
            return '——吉——\n' f'{random.choice(qianwens["吉"])}\n\n' f'今天的幸运物是：{random.choice(lucky_things["吉"])}'
        case '末吉':
            return '——末吉——\n' f'{random.choice(qianwens["末吉"])}\n\n' f'今天的幸运物是：{random.choice(lucky_things["凶"])}'
        case '凶':
            return '——凶——\n' f'{random.choice(qianwens["凶"])}\n\n' f'今天的幸运物是：{random.choice(lucky_things["凶"])}'
        case '大凶':
            return '——大凶——\n' f'{random.choice(qianwens["凶"])}\n\n' f'今天的幸运物是：{random.choice(lucky_things["凶"])}'
        case _:
            return ''


@io_bound
def read_data(qq: str) -> Tuple[bool, int, str]:
    """
    在文件中读取指定QQ今日已生成过的随机数，若今日未生成，则新生成一个随机数并写入文件
    """
    data_file_path = Path(data_path, f'jrrp_{datetime.datetime.now().strftime("%Y-%m-%d")}.json')
    try:
        with open(data_file_path, 'r', encoding='utf-8') as fp:  # 以 追加+读 的方式打开文件
            f_data = fp.read()
            if len(f_data) > 0:
                data: dict = json.loads(f_data)  # 读写
            else:
                data = {}
    except FileNotFoundError:
        data = {}
    if data:  # 若文件为空，则生成一个随机数并写入到文件中，然后返回生成的随机数
        renpin = random.randint(0, 100)
        qianwen = gen_qianwen(renpin)
        data[qq] = {'renpin': renpin, 'qianwen': qianwen}
        with open(data_file_path, 'wb') as fp:
            fp.write(
                json.dumps(
                    data, option=json.OPT_INDENT_2 | json.OPT_APPEND_NEWLINE
                )
            )
        return True, renpin, qianwen
    if qq in data:  # 若文件中有指定QQ的数据则读取并返回
        return False, data[qq]['renpin'], data[qq]['qianwen']
    else:  # 若文件中没有指定QQ的数据，则生成一个随机数并写入到文件中，然后返回生成的随机数
        renpin = random.randint(0, 100)
        qianwen = gen_qianwen(renpin)
        data[qq] = {'renpin': renpin, 'qianwen': qianwen}
        with open(data_file_path, 'wb') as fp:
            fp.write(
                json.dumps(
                    data, option=json.OPT_INDENT_2 | json.OPT_APPEND_NEWLINE
                )
            )
        return True, renpin, qianwen
