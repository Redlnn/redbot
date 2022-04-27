#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from graia.broadcast import Broadcast
from uvicorn.config import Config
from uvicorn.server import Server


class NoSignalServer(Server):
    """不注册 Signal 的 Uvicorn 服务器"""

    def install_signal_handlers(self) -> None:
        return


class FastApiCore:
    server: NoSignalServer
    asgi: FastAPI
    fetch_task: asyncio.Task | None = None

    def __init__(
        self,
        app: FastAPI | None = None,
        listen_host: str = 'localhost',
        listen_port: int = 8000,
        log: bool = True,
        **config_kwargs,
    ):
        """初始化 FastApiCore
        Args:
            app (Optional[FastAPI], optional): ASGI 应用. Defaults to None.
            log (bool, optional): 是否启用连接日志. Defaults to True.
            listen_host (str, optional): 服务地址. Defaults to localhost.
            listen_port (int, optional): 服务端口. Defaults to 8000.
            **config_kwargs (Any, optional): 额外配置参数. Defaults to {}.
        """
        self.asgi = app or FastAPI()
        self.asgi.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        LOG_CONFIG = {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "default": {
                    "class": "graia.ariadne.util.LoguruHandler",
                },
            },
            "loggers": {
                "uvicorn.error": {"handlers": ["default"] if log else [], "level": "INFO"},
                "uvicorn.access": {"handlers": ["default"] if log else [], "level": "INFO"},
                "uvicorn.asgi": {"handlers": ["default"] if log else [], "level": "INFO"},
            },
        }
        self.server = NoSignalServer(
            Config(self.asgi, host=listen_host, port=listen_port, log_config=LOG_CONFIG, **config_kwargs)
        )

    async def start(self):
        """启动 Uvicorn 服务器"""
        self.fetch_task = asyncio.create_task(self.server.serve())

    async def stop(self) -> None:
        """停止 Uvicorn 服务器"""
        self.server.should_exit = True
        if self.fetch_task is None:
            return
        try:
            await asyncio.wait_for(self.fetch_task, timeout=5.0)
        except asyncio.TimeoutError:
            self.server.force_exit = True
        await self.fetch_task
        self.fetch_task = None
