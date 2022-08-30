#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from typing import Any, AsyncIterator, Optional

from launart import ExportInterface, Service
from loguru import logger
from playwright.__main__ import main
from playwright.async_api import Browser, Page, Playwright, async_playwright


def install_playwright():
    """自动安装、更新 Chromium"""

    def restore_env():
        del os.environ["PLAYWRIGHT_DOWNLOAD_HOST"]

    logger.info("正在检查 Chromium 更新")
    sys.argv = ["", "install", "chromium"]
    os.environ["PLAYWRIGHT_DOWNLOAD_HOST"] = "https://playwright.sk415.workers.dev"
    success = False
    try:
        main()
    except SystemExit as e:
        if e.code == 0:
            success = True
    if not success:
        logger.info("Chromium 更新失败，尝试从原始仓库下载，速度较慢")
        os.environ["PLAYWRIGHT_DOWNLOAD_HOST"] = ""
        try:
            main()
        except SystemExit as e:
            if e.code != 0:
                restore_env()
                raise RuntimeError("未知错误，Chromium 下载失败")
    restore_env()


class ChromiumBrowser:
    browser: Optional[Browser] = None
    playwright: Optional[Playwright] = None

    def __init__(self):
        ...

    async def init(self, **kwargs):
        if self.playwright is not None:
            raise RuntimeError('浏览器已经初始化')
        if self.browser is not None:
            raise RuntimeError('浏览器已经初始化')
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(**kwargs)

    async def get(self) -> Browser:
        if self.browser is not None:
            return self.browser
        raise RuntimeError('浏览器尚未初始化')

    async def get_new_page(self, **kwargs) -> AsyncIterator[Page]:
        browser = await self.get()
        page = await browser.new_page(**kwargs)
        try:
            yield page
        finally:
            await page.close()

    async def close(self):
        if self.browser is not None:
            await self.browser.close()
        if self.playwright is not None:
            await self.playwright.stop()


class ChromiumBrowserProvider(ExportInterface):
    browser: ChromiumBrowser

    def __init__(self, browser):
        self.browser = browser
        super().__init__()

    async def get(self) -> Browser:
        return await self.browser.get()


class ChromiumBrowserService(Service):
    id = 'browser/chromium'
    supported_interface_types = {ChromiumBrowserProvider}
    browser: ChromiumBrowser
    kwargs: dict[str, Any]

    def __init__(self, **kwargs) -> None:
        self.browser = ChromiumBrowser()
        self.kwargs = kwargs
        super().__init__()

    def get_interface(self, interface_type):
        if issubclass(interface_type, ChromiumBrowserProvider):
            return ChromiumBrowserProvider(self.browser)
        raise ValueError(f'unsupported interface type {interface_type}')

    @property
    def required(self):
        return set()

    @property
    def stages(self):
        return {'preparing', 'cleanup'}

    async def launch(self, _):
        install_playwright()
        async with self.stage('preparing'):
            await self.browser.init(**self.kwargs)
            self.kwargs = {}
        # async with self.stage('blocking'):
        #     await _.status.wait_for_sigexit()
        async with self.stage('cleanup'):
            await self.browser.close()
