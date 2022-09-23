#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime

from graiax.text2img.playwright import html2img as _html2img
from graiax.text2img.playwright.builtin import md2img as _md2img
from graiax.text2img.playwright.builtin import text2img as _text2img
from graiax.text2img.playwright.types import PageParms, ScreenshotParms

footer = (
    '<style>.footer{box-sizing:border-box;position:absolute;left:0;width:100%;background:#eee;'
    'padding:50px 40px;margin-top:50px;font-size:0.85rem;color:#6b6b6b;}'
    '.footer p{margin:5px auto;}</style>'
    f'<div class="footer"><p>由 RedBot 生成</p><p>{datetime.now().strftime("%Y/%m/%d %p %I:%M:%S")}</p></div>'
)


async def text2img(text: str, width: int = 800) -> bytes:
    html = await _text2img(text, return_html=True)
    html += footer

    return await _html2img(
        html,
        page_parms=PageParms(viewport={'width': width, 'height': 10}, device_scale_factor=1.5),
        screenshot_parms=ScreenshotParms(type='jpeg', quality=80, full_page=True, scale='device'),
    )


async def md2img(text: str, width: int = 800, extra_css: str = '') -> bytes:
    html = await _md2img(text, extra_css=extra_css, return_html=True)
    html += footer

    return await _html2img(
        html,
        page_parms=PageParms(viewport={'width': width, 'height': 10}, device_scale_factor=1.5),
        screenshot_parms=ScreenshotParms(type='jpeg', quality=80, full_page=True, scale='device'),
    )
