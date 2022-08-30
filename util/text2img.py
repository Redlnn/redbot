#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path

from aiofile import async_open
from graia.ariadne.app import Ariadne
from jinja2 import Template
from launart import Launart
from markdown import markdown
from playwright.async_api import BrowserContext, Page

from util.browser import ChromiumBrowserProvider


class GetPage:
    launart: Launart
    context: BrowserContext
    page: Page
    width: int

    def __init__(self, width):
        ariadne = Ariadne.current()
        self.launart = ariadne.launch_manager
        self.width = width

    async def __aenter__(self):
        browser = await self.launart.get_interface(ChromiumBrowserProvider).get()
        self.context = await browser.new_context(
            viewport={'width': int(self.width / 1.5), 'height': 10}, device_scale_factor=1.5
        )
        self.page = await self.context.new_page()
        return self.page

    async def __aexit__(self, type, value, trace):
        await self.page.close()
        await self.context.close()


async def text2img(text: str, width: int = 1000) -> bytes:
    async with async_open(Path(__file__).parent / 'browser' / 'template' / 'text2img.min.html') as f:
        template: str = await f.read()
    template = template.replace('{{content}}', text)
    template = template.replace('{{extra1}}', '由 Redbot 生成')
    text = template.replace('{{extra2}}', datetime.now().strftime('%Y/%m/%d %H:%M:%S'))

    async with GetPage(width) as page:
        await page.set_content(text)
        img = await page.screenshot(type='jpeg', quality=80, full_page=True, scale='device')
    return img


async def md2img(md: str, width: int = 1000) -> bytes:
    md = markdown(md)

    async with async_open(Path(__file__).parent / 'browser' / 'template' / 'text2img.min.html') as f:
        template: str = await f.read()
    template = template.replace('{{content}}', md)
    template = template.replace('{{extra1}}', '由 Redbot 生成')
    md = template.replace('{{extra2}}', datetime.now().strftime('%Y/%m/%d %H:%M:%S'))

    async with GetPage(width) as page:
        await page.set_content(md)
        img = await page.screenshot(type='jpeg', path='1.jpg', quality=80, full_page=True, scale='device')
    return img


async def template2img() -> bytes:
    ...
