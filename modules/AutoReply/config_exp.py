#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
请不要直接修改此文件，请将本文件复制一份并重命名为 "config.py" 后再修改 "config.py"

图片回复请支持本地图片
"""

from .utils import img_2_bytesio  # noqa
from config import config_data

disabled = False if config_data['Modules']['AutoReply']['Enabled'] else True

# 格式
# reply = {
#     要生效的群号: {
#         '关键词': ['内容'],
#     }
# }

# 全文匹配自动回复
reply: dict = {
    123456789: {
        # '自动回复关键词': ['纯文本'],
        # '带图回复关键词': ['文本1', await img_2_bytesio(r'C:\1.jpg'), '文本2'],
        # '图片回复关键词': [await img_2_bytesio(r'C:\1.jpg')]
    }
}

# 正则匹配自动回复
re_reply: dict = {
    123456789: {
        # r'^\d$': ['内容']
    }
}

# 模糊匹配自动回复（只要消息中包含关键词就回复）
fuzzy_reply: dict = {
    123456789: {
        # '关键词': ['内容']
    }
}
