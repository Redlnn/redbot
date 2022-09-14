#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from io import BytesIO
from pathlib import Path

import httpx
from graia.ariadne.util.async_exec import cpu_bound
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from PIL.ImageFont import FreeTypeFont
from pydantic import BaseModel

Ink = str | int | tuple[int, int, int] | tuple[int, int, int, int]


class Reward(BaseModel):
    """奖励"""

    name: str | None = None
    """奖励名称"""

    num: int
    """奖励数量"""

    ico: str | Path | None = None
    """奖励图标"""


def get_qlogo(qq_id: int) -> bytes:
    """获取QQ头像
    Args:
        qq_id (int): QQ号
    Returns:
        bytes: 图片二进制数据
    """
    resp = httpx.get(f'http://q1.qlogo.cn/g?b=qq&nk={qq_id}&s=640')
    return resp.content


def get_time() -> str:
    """获取格式化后的当前时间"""
    return time.strftime('%Y/%m/%d %p %I:%M:%S', time.localtime())


def cut_text(
    font: FreeTypeFont,
    origin: str,
    chars_per_line: int,
):
    """将单行超过指定长度的文本切割成多行
    Args:
        font (FreeTypeFont): 字体
        origin (str): 原始文本
        chars_per_line (int): 每行字符数（按全角字符算）
    """
    target = ''
    start_symbol = '[{<(【《（〈〖［〔“‘『「〝'
    end_symbol = ',.!?;:]}>)%~…，。！？；：】》）〉〗］〕”’～』」〞'
    line_width = chars_per_line * font.getlength('一')
    for i in origin.splitlines(False):
        if i == '':
            target += '\n'
            continue
        j = 0
        for ind, elem in enumerate(i):
            if i[j : ind + 1] == i[j:]:
                target += i[j : ind + 1] + '\n'
                continue
            elif font.getlength(i[j : ind + 1]) <= line_width:
                continue
            elif ind - j > 3:
                if i[ind] in end_symbol and i[ind - 1] != i[ind]:
                    target += i[j : ind + 1] + '\n'
                    j = ind + 1
                    continue
                elif i[ind] in start_symbol and i[ind - 1] != i[ind]:
                    target += i[j:ind] + '\n'
                    continue
            target += i[j:ind] + '\n'
            j = ind
    return target.rstrip()


def exp_bar(w: int, h: int, rato: float, bg: Ink = 'black', fg: Ink = 'white') -> Image.Image:
    """获取一个经验条的图片对象
    Args:
        w (int): 宽度
        h (int): 高度
        rato (float): 比例
        bg (_Ink): 背景颜色
        fg (_Ink): 前景颜色
    Returns:
        Image.Image: 图片对象
    """
    origin_w = w
    origin_h = h
    w *= 4
    h *= 4
    bar_canvase = Image.new('RGBA', (w, h), '#00000000')
    bar_draw = ImageDraw.Draw(bar_canvase)
    # draw background
    draw_exp_bar_and_bg(bar_draw, h, bg, w)
    # draw exp bar
    draw_exp_bar_and_bg(bar_draw, h, fg, w * rato if rato <= 1 else w)
    return bar_canvase.resize((origin_w, origin_h), Image.LANCZOS)


def draw_exp_bar_and_bg(bar_draw, h, fill, w):
    bar_draw.ellipse((0, 0, h, h), fill=fill)
    bar_draw.ellipse((w - h, 0, w, h), fill=fill)
    bar_draw.rectangle((h // 2, 0, w - h // 2, h), fill=fill)


PLACEHOLDER = '本常量用于获取字符高度'


@cpu_bound
def get_signin_img(
    qq: int,
    name: str,
    level: int,
    exp: tuple[int, int],
    total_days: int,
    consecutive_days: int,
    is_signin_consecutively: bool,
    rewards: list[Reward],
    font_path: str,
    text_color: Ink = 'white',
    exp_bar_fg_color: Ink = '#80d0f1',
    exp_bar_bg_color: Ink = '#00000055',
) -> bytes:
    """生成一张签到打卡图，应该算 CPU 密集型任务，因此 httpx 并没有使用 asyncio 如有需要可自行魔改
    Args:
        qq (int): QQ号
        name (str): 群名片
        level (int): 好感等级
        exp (tuple[int, int]): 好感经验值，请使用 (当前经验值, 总所需经验值) 的格式传入
        total_days (int): 累计签到天数
        consecutive_days (int): 连续签到天数
        is_signin_consecutively (bool): 是否连续签到
        rewards (list[Reward]): 签到奖励
        font_path (str): 字体路径
        text_color (_In): 文字颜色
        exp_bar_fg_color (_Ink): 经验条前景色
        exp_bar_bg_color (_Ink): 经验条背景色
    Returns:
        bytes: 生成结果的图片二进制数据
    """
    size = (1920, 1080)
    avatar_size = 384
    avatar_xy = int(size[1] * 0.15)

    canvas = Image.new('RGB', size, '#FFFFFF')
    draw = ImageDraw.Draw(canvas)

    qlogo = Image.open(BytesIO(get_qlogo(qq_id=qq)))
    # qlogo = Image.open('3.jpg')

    # 背景
    if size[1] > size[0]:
        qlogo1 = qlogo.resize((size[1], size[1]), Image.LANCZOS).filter(ImageFilter.GaussianBlur(radius=50))
        canvas.paste(qlogo1, ((size[0] - size[1]) // 2, 0))
    else:
        qlogo1 = qlogo.resize((size[0], size[0]), Image.LANCZOS).filter(ImageFilter.GaussianBlur(radius=50))
        canvas.paste(qlogo1, (0, (size[1] - size[0]) // 2))

    # 背景加一层黑
    mask = Image.new('RGBA', size, '#00000055')
    canvas.paste(mask, (0, 0), mask.split()[3])

    # 魔法阵
    mahojin_size_offset = 55  # 魔法阵比头像大多少（半径）
    mahojin_size = avatar_size + 2 * mahojin_size_offset
    mahojin = Image.open(Path(__file__) / 'imgs' / 'mahojin.png')
    mahojin = mahojin.resize((mahojin_size, mahojin_size), Image.LANCZOS)
    canvas.paste(mahojin, (avatar_xy - mahojin_size_offset, avatar_xy - mahojin_size_offset), mask=mahojin.split()[3])

    # 头像描边
    stroke_width = 5  # 描边厚度
    stroke = Image.new(
        'RGBA', ((avatar_size + 2 * stroke_width) * 4, (avatar_size + 2 * stroke_width) * 4), '#00000000'
    )
    stroke_draw = ImageDraw.Draw(stroke)
    stroke_draw.ellipse(
        (0, 0, (avatar_size + 2 * stroke_width) * 4, (avatar_size + 2 * stroke_width) * 4), fill='#000000bb'
    )
    stroke = stroke.resize((avatar_size + 2 * stroke_width, avatar_size + 2 * stroke_width), Image.LANCZOS)
    canvas.paste(stroke, (avatar_xy - stroke_width, avatar_xy - stroke_width), mask=stroke.split()[3])

    # 圆形头像蒙版
    avatar_mask = Image.new('RGBA', (avatar_size * 4, avatar_size * 4), '#00000000')
    avatar_mask_draw = ImageDraw.Draw(avatar_mask)
    avatar_mask_draw.ellipse((0, 0, avatar_size * 4, avatar_size * 4), fill='#000000ff')
    avatar_mask = avatar_mask.resize((avatar_size, avatar_size), Image.LANCZOS)

    # 圆形头像
    qlogo2 = qlogo.resize((avatar_size, avatar_size), Image.LANCZOS)
    canvas.paste(qlogo2, (avatar_xy, avatar_xy), avatar_mask)

    font_1 = ImageFont.truetype(font_path, size=60)
    font_2 = ImageFont.truetype(font_path, size=35)
    font_3 = ImageFont.truetype(font_path, size=45)
    qq_text = f'QQ：{qq}'
    impression = f'经验等级：Lv{level}  {exp[0]} / {exp[1]}'

    y = avatar_xy + 25

    draw.text((2 * avatar_xy + avatar_size, y), name, font=font_1, fill=text_color)
    y += font_1.getsize(name)[1] + 50
    draw.text((2 * avatar_xy + avatar_size, y), qq_text, font=font_2, fill=text_color)
    y += font_2.getsize(qq_text)[1] + 30
    draw.text((2 * avatar_xy + avatar_size, y), impression, font=font_2, fill=text_color)
    bar = exp_bar(font_2.getsize(impression)[0], 6, exp[0] / exp[1], fg=exp_bar_fg_color, bg=exp_bar_bg_color)
    canvas.paste(bar, (2 * avatar_xy + avatar_size, y + font_2.getsize(impression)[1] + 10), mask=bar.split()[3])

    y = avatar_xy + avatar_size + 100
    draw.text((avatar_xy + 30, y), f'共签到 {total_days} 天', font=font_3, fill=text_color)

    if is_signin_consecutively:
        y += font_3.getsize(PLACEHOLDER)[1] + 20
        draw.text((avatar_xy + 30, y), f'连续签到 {consecutive_days} 天', font=font_3, fill=text_color)
    y += font_3.getsize(PLACEHOLDER)[1] + 30
    for reward in rewards:
        x_offset = avatar_xy + 30
        if reward.ico is not None:
            ico = Image.open(reward.ico).convert('RGBA')
            ico = ico.resize((font_2.getsize(PLACEHOLDER)[1], font_2.getsize(PLACEHOLDER)[1]), Image.LANCZOS)
            canvas.paste(ico, (x_offset, y + 5), mask=ico.split()[3])
            x_offset = x_offset + 20 + ico.size[0]
        if reward.name is not None:
            draw.text((x_offset, y), f'{reward.name} +{reward.num}', font=font_2, fill=text_color)
        else:
            draw.text((x_offset, y), f'+{reward.num}', font=font_2, fill=text_color)
        y += font_2.getsize(PLACEHOLDER)[1] + 30

    # 一言背景
    hitokoto_bg = Image.new('RGBA', (1045, 390), '#00000000')
    hitokoto_bg_draw = ImageDraw.Draw(hitokoto_bg)
    hitokoto_bg_draw.rounded_rectangle((0, 0, 1045, 390), 20, fill='#00000030')
    hitokoto_bg = hitokoto_bg.resize((1045, 390), Image.LANCZOS)
    canvas.paste(hitokoto_bg, (2 * avatar_xy + avatar_size, avatar_xy + avatar_size + 55), mask=hitokoto_bg.split()[3])

    # 获取一言
    try:
        hotokoto = httpx.get('https://api.dzzui.com/api/yiyan', timeout=3)
    except Exception as e:
        hotokoto = '一言获取失败'
        print(e)
    else:
        hotokoto = hotokoto.text
    # hotokoto = '由于一言目前属于公益性运营，为了保证资源的公平利用和不过度消耗公益资金，我们会定期的屏蔽某些大流量的站点。若您的站点的流量较大，您需要提前联系我们获得授权后再开始使用。对于超过阈值的站点，我们有可'
    font_4 = ImageFont.truetype(font_path, size=45)
    draw.text(
        (2 * avatar_xy + avatar_size + 50, avatar_xy + avatar_size + 100),
        cut_text(font_4, hotokoto, 21),
        font=font_4,
        fill=text_color,
        spacing=10,
    )  # 最大不要超过5行

    # footer
    font_5 = ImageFont.truetype(font_path, size=15)
    draw.text((15, size[1] - 55), f'RedBot ©2022\n{get_time()}', font=font_5, fill='#cccccc')

    # canvas.show()  # 直接展示生成结果（保存为临时文件）

    canvas.convert('RGB')
    byte_io = BytesIO()
    canvas.save(
        byte_io,
        format='JPEG',
        quality=90,
        optimize=True,
        progressive=True,
        subsampling=2,
        qtables='web_high',
    )
    return byte_io.getvalue()
