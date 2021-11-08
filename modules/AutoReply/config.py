#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import BytesIO


async def _img_2_bytesio(img_path: str):
    with open(img_path, 'rb') as f:
        content = f.read()
    return BytesIO(content).getvalue()


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
        # '带图回复关键词': ['文本1', await _img_2_bytesio(r'C:\1.jpg'), '文本2'],
        # '图片回复关键词': [await _img_2_bytesio(r'C:\1.jpg')]
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
