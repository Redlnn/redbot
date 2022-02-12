#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
仿锤子便签的文字转图片
"""

import os
import time
from io import BytesIO
from pathlib import Path

from graia.ariadne.util.async_exec import cpu_bound
from PIL import Image as Img
from PIL import ImageDraw, ImageFont

from util.config import BasicConfig
from util.path import root_path

__all__ = ['async_generate_img', 'generate_img', 'hr']

basic_cfg = BasicConfig()

_font_name: str = 'sarasa-mono-sc-semibold.ttf'
_font_path = Path(root_path, 'fonts', _font_name)  # 字体文件的路径
if not _font_path.exists():
    raise ValueError(f'文本转图片所用的字体文件不存在，请检查配置文件，尝试访问的路径如下：↓\n{_font_path}')
if len(_font_name) <= 4 or _font_name[-4:] not in ('.ttf', '.ttc', '.otf', '.otc'):
    raise ValueError('所配置的字体文件名不正确，请检查配置文件')
_font_path = str(_font_path)

_is_ttc_font = False
_ttc_font_index = 1
_font_size = 50
_font_color = '#645647'
_line_space = 30
_text_margin = 80
_chars_per_line = 27

hr = _chars_per_line * '—'

_background_color = '#fffcf6'
_border_side_margin = 50
_border_top_margin = 70
_border_bottom_margin = 250
_border_interval = 5
_border_square_wrap_width = 5
_border_outline_width = 5  # 内描边
_border_outline_color = '#e9e5d9'

if _is_ttc_font:
    font = ImageFont.truetype(_font_path, size=_font_size, index=_ttc_font_index)  # 确定正文用的ttf字体
    extra_font = ImageFont.truetype(
        _font_path, size=_font_size - int(0.3 * _font_size), index=_ttc_font_index
    )  # 确定而额外文本用的ttf字体
else:
    # 确定正文用的ttf字体
    font = ImageFont.truetype(_font_path, size=_font_size)
    # 确定而额外文本用的ttf字体
    extra_font = ImageFont.truetype(_font_path, size=_font_size - int(0.3 * _font_size))


def _get_time(mode: int = 1) -> str:
    """
    返回当前时间
    """
    time_now = int(time.time())
    time_local = time.localtime(time_now)
    if mode == 2:
        dt = time.strftime('%Y-%m-%d_%H-%M-%S', time_local)
    else:
        dt = time.strftime('%Y-%m-%d %H:%M:%S', time_local)
    return dt


def _cut_text(
    origin: str,
    line_width: int,
):
    target = ''
    start_symbol = '[{<(【《（〈〖［〔“‘『「〝'
    end_symbol = ',.!?;:]}>)%~…，。！？；：】》）〉〗］〕”’～』」〞'
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


@cpu_bound
def async_generate_img(text_and_img: list[str | bytes] = None, chars_per_line: int = _chars_per_line) -> bytes:
    return generate_img(text_and_img, chars_per_line)


def generate_img(text_and_img: list[str | bytes] = None, chars_per_line: int = _chars_per_line) -> bytes:
    """
    根据输入的文本，生成一张图并返回图片文件的路径

    - 本地文件转 bytes 方法：BytesIO(open('1.jpg', 'rb').getvalue())
    - 网络文件转 bytes 方法：requests.get('http://localhost/1.jpg'.content)

    :param text_and_img: 要放到图里的文本（str）/图片（bytes）
    :param chars_per_line: 每行几个字
    :return: 图片文件的路径
    """

    if not text_and_img:
        raise ValueError('ArgumentError: 参数内容为空')
    elif not isinstance(text_and_img, list):
        raise ValueError('ArgumentError: 参数类型错误')

    extra_text1 = f'由 {basic_cfg.admin.masterName} の {basic_cfg.botName} 生成'  # 额外文本1
    extra_text2 = _get_time()  # 额外文本2

    line_width = int(chars_per_line * font.getlength('一'))  # 行宽 = 每行全角宽度的字符数 * 一个字符框的宽度

    content_height = 0
    contents: list = []
    # contents = [{
    #     'content': str/Img.Image,
    #     'height': 区域高度
    # }]

    for i in text_and_img:
        if isinstance(i, str):
            text = _cut_text(i.replace('{hr}', chars_per_line * '—'), line_width)
            text_height = font.getsize_multiline(text, spacing=_line_space)[1]
            contents.append({'content': text, 'height': text_height})
            content_height += text_height + _line_space
            del text_height
        elif isinstance(i, bytes):
            img: Img.Image = Img.open(BytesIO(i))
            img_height = int(line_width / img.size[0] * img.size[1])
            img = img.resize((line_width, img_height), Img.LANCZOS)
            contents.append({'content': img, 'height': img_height})
            content_height += img_height + (2 * _line_space)
            del img_height

    # 画布高度=(内容区域高度+(2*正文边距)+(边框上边距+4*边框厚度+2*内外框距离+边框下边距)
    bg_height = (
        content_height
        + (2 * _text_margin)
        + (_border_top_margin + (4 * _border_outline_width) + (2 * _border_interval))
        + _border_bottom_margin
        + _line_space
    )
    # 画布宽度=行宽+2*正文侧面边距+2*(边框侧面边距+(2*边框厚度)+内外框距离)
    bg_width = (
        line_width + (2 * _text_margin) + (2 * (_border_side_margin + (2 * _border_outline_width) + _border_interval))
    )

    canvas = Img.new('RGB', (bg_width, bg_height), _background_color)
    draw = ImageDraw.Draw(canvas)
    # 从这里开始绘图均为(x, y)坐标，横坐标x，纵坐标y
    # rectangle(起点坐标, 终点坐标) 绘制矩形，且方向必须为从左上到右下

    # 绘制外框
    # 外框左上点坐标 x=边框侧边距 y=边框上边距
    # 外框右下点坐标 x=画布宽度-边框侧边距 y=画布高度-边框上边距
    draw.rectangle(
        (
            (_border_side_margin, _border_top_margin),
            (bg_width - _border_side_margin, bg_height - _border_bottom_margin),
        ),
        fill=None,
        outline=_border_outline_color,
        width=_border_outline_width,
    )
    # 绘制内框
    # 内框左上点坐标 x=边框侧边距+外边框厚度+内外框距离 y=边框上边距+外边框厚度+内外框距离
    # 内框右下点坐标 x=画布宽度-边框侧边距-外边框厚度-内外框距离 y=画布高度-边框上边距-外边框厚度-内外框距离
    draw.rectangle(
        (
            (
                _border_side_margin + _border_outline_width + _border_interval,
                _border_top_margin + _border_outline_width + _border_interval,
            ),
            (
                bg_width - _border_side_margin - _border_outline_width - _border_interval,
                bg_height - _border_bottom_margin - _border_outline_width - _border_interval,
            ),
        ),
        fill=None,
        outline=_border_outline_color,
        width=_border_outline_width,
    )

    pil_compensation = _border_outline_width - 1 if _border_outline_width > 1 else 0

    # 绘制左上小方形
    # 左上点坐标 x=边框侧边距-边长-2*边框厚度+补偿 y=边框侧边距-边长-2*边框厚度+补偿 (补偿PIL绘图的错位)
    # 右下点坐标 x=边框侧边距+补偿 y=边框上边距+补偿
    draw.rectangle(
        (
            (
                _border_side_margin - _border_square_wrap_width - (2 * _border_outline_width) + pil_compensation,
                _border_top_margin - _border_square_wrap_width - (2 * _border_outline_width) + pil_compensation,
            ),
            (
                _border_side_margin + pil_compensation,
                _border_top_margin + pil_compensation,
            ),
        ),
        fill=None,
        outline=_border_outline_color,
        width=_border_outline_width,
    )
    # 绘制右上小方形
    # 左上点坐标 x=画布宽度-(边框侧边距+补偿) y=边框侧边距-边长-2*边框厚度+补偿 (补偿PIL绘图的错位)
    # 右下点坐标 x=画布宽度-(边框侧边距-边长-2*边框厚度+补偿) y=边框上边距+补偿
    draw.rectangle(
        (
            (
                bg_width - _border_side_margin - pil_compensation,
                _border_top_margin - _border_square_wrap_width - (2 * _border_outline_width) + pil_compensation,
            ),
            (
                bg_width
                - _border_side_margin
                + _border_square_wrap_width
                + (2 * _border_outline_width - pil_compensation),
                _border_top_margin + pil_compensation,
            ),
        ),
        fill=None,
        outline=_border_outline_color,
        width=_border_outline_width,
    )
    # 绘制左下小方形
    # 左上点坐标 x=边框侧边距-边长-2*边框厚度+补偿 y=画布高度-(边框下边距+补偿) (补偿PIL绘图的错位)
    # 右下点坐标 x=边框侧边距+补偿 y=画布高度-(边框侧边距-边长-2*边框厚度+补偿)
    draw.rectangle(
        (
            (
                _border_side_margin - _border_square_wrap_width - (2 * _border_outline_width) + pil_compensation,
                bg_height - _border_bottom_margin - pil_compensation,
            ),
            (
                _border_side_margin + pil_compensation,
                bg_height
                - _border_bottom_margin
                + _border_square_wrap_width
                + (2 * _border_outline_width)
                - pil_compensation,
            ),
        ),
        fill=None,
        outline=_border_outline_color,
        width=_border_outline_width,
    )
    # 绘制右下小方形
    # 左上点坐标 x=画布宽度-(边框侧边距+补偿) y=画布高度-(边框下边距+补偿) (补偿PIL绘图的错位)
    # 右下点坐标 x=画布宽度-(边框侧边距-边长-2*边框厚度+补偿) y=画布高度-(边框侧边距-边长-2*边框厚度+补偿)
    draw.rectangle(
        (
            (
                bg_width - _border_side_margin - pil_compensation,
                bg_height - _border_bottom_margin - pil_compensation,
            ),
            (
                bg_width
                - _border_side_margin
                + _border_square_wrap_width
                + (2 * _border_outline_width - pil_compensation),
                bg_height
                - _border_bottom_margin
                + _border_square_wrap_width
                + (2 * _border_outline_width)
                - pil_compensation,
            ),
        ),
        fill=None,
        outline=_border_outline_color,
        width=_border_outline_width,
    )

    # 绘制内容
    # 开始坐标:
    # x=边框侧边距+2*边框厚度+内外框距离+正文侧边距
    # y=边框上边距+2*边框厚度+内外框距离+正文上边距+行号*(行高+行距)
    content_area_x = _border_side_margin + (2 * _border_outline_width) + _border_interval + _text_margin
    content_area_y = _border_top_margin + (2 * _border_outline_width) + _border_interval + _text_margin - 7

    content_area_y += _line_space

    for i in contents:
        if isinstance(i['content'], str):
            draw.text(
                (content_area_x, content_area_y),
                i['content'],
                fill=_font_color,
                font=font,
                spacing=_line_space,
            )
            content_area_y += i['height'] + _line_space
        elif isinstance(i['content'], Img.Image):
            canvas.paste(i['content'], (content_area_x, content_area_y + _line_space))
            content_area_y += i['height'] + (2 * _line_space)

    # 绘制第一行额外文字
    # 开始坐标 x=边框侧边距+(4*内外框距离) y=画布高度-边框下边距+(2*内外框距离)
    draw.text(
        (
            _border_side_margin + (4 * _border_interval),
            bg_height - _border_bottom_margin + (2 * _border_interval),
        ),
        extra_text1,
        fill='#b4a08e',
        font=extra_font,
    )
    # 绘制第二行额外文字
    # 开始坐标 x=边框侧边距+(4*内外框距离) y=画布高度-边框下边距+(3*内外框距离)+第一行额外文字的高度
    draw.text(
        (
            _border_side_margin + (4 * _border_interval),
            bg_height - _border_bottom_margin + (3 * _border_interval) + extra_font.getsize(extra_text1)[1],
        ),
        extra_text2,
        fill='#b4a08e',
        font=extra_font,
    )

    # canvas = canvas.convert(mode='RGB')  # 将RGBA转换为RGB
    # canvas.show()  # 展示生成结果

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

    # 保存为jpg图片 https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html?highlight=subsampling#jpeg
    # img_name = 'temp_{}.jpg'.format(_get_time(2))  # 自定义临时文件的保存名称
    # img_path = os.path.join(img_name)  # 自定义临时文件保存路径
    # canvas.save(
    #     img_path,
    #     format='JPEG',
    #     quality=90,
    #     optimize=True,
    #     progressive=True,
    #     subsampling=2,
    #     qtables='web_high'
    # )

    # 保存为png图片 https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html?highlight=subsampling#png
    # img_name = 'temp_{}.png'.format(__get_time(2))  # 自定义临时文件的保存名称
    # img_path = os.path.join(temp_dir_path, img_name)  # 自定义临时文件保存路径
    # canvas.save(img_path, format='PNG', optimize=True)

    return byte_io.getvalue()
