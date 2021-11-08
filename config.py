#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import List

# bot管理者QQ号
master: int = 731347477


@dataclass
class BotConfig:
    host: str = 'http://localhost:8080'
    verify_key: str = 'verifyKey'
    account: int = 123456789
    enable_log_chat: bool = True
    debug: bool = False


@dataclass
class DatabaseConfig:
    database: str = 'redbot'  # 数据库名称
    mysql: bool = False
    mysql_host: str = 'localhost'
    mysql_port: int = 3306
    mysql_user: str = 'user'
    mysql_passwd: str = 'password'


@dataclass
class BlackList:
    user: List[int] = ()
    group: List[int] = ()


@dataclass
class Text2Img:
    # 字体文件的文件名（带后缀名），支持ttf/otf/ttc/otc
    # 字体文件请放在跟目录的 fonts 文件夹内
    font_name: str = 'OPPOSans.ttf'
    # 若使用ttc/otc字体文件，则填写要加载的ttc/otc的字形索引号，不懂请填1
    # 具体索引号可安装 afdko 后使用 `otc2otf -r {name}.ttc`查看
    # afdko: https://github.com/adobe-type-tools/afdko
    ttc_font_index: int = 1
    font_size: int = 50  # 字体大小
    font_color: str = '#645647'  # 字体颜色
    line_space: int = 30  # 行间距
    chars_per_line: int = 25  # 每行长度（单位：字符数量，以中文字符为准）
    text_margin: int = 80  # 文字范围到内框的距离
    background_color: str = '#fffcf6'  # 背景颜色
    border_side_margin: int = 50  # 外框距左右边界距离
    border_top_margin: int = 70  # 外框距上边界距离
    border_bottom_margin: int = 250  # 外框距下边界距离
    border_interval: int = 5  # 内外框距离
    border_nook_wrap_width: int = 5  # 外边框四角的小正方形边长
    border_outline_width: int = 5  # 边框描边（内描边）厚度
    border_outline_color: str = '#e9e5d9'  # 边框颜色
