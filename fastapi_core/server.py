#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import signal
import socket

import click
from uvicorn.server import Server

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)


class ModifiedServer(Server):
    async def serve(self, sockets: list[socket.socket] | None = None) -> None:
        # 魔改 —— Start
        logger = logging.getLogger('uvicorn.error')
        self.shutdown_status = False
        # 魔改 —— End

        process_id = os.getpid()

        config = self.config
        if not config.loaded:
            config.load()

        self.lifespan = config.lifespan_class(config)

        # 魔改 —— Start
        # self.install_signal_handlers()
        # 魔改 —— End

        message = "Started server process [%d]"
        color_message = "Started server process [" + click.style("%d", fg="cyan") + "]"
        logger.info(message, process_id, extra={"color_message": color_message})

        await self.startup(sockets=sockets)
        if self.should_exit:
            return
        await self.main_loop()
        await self.shutdown(sockets=sockets)

        message = "Finished server process [%d]"
        color_message = "Finished server process [" + click.style("%d", fg="cyan") + "]"
        logger.info(message, process_id, extra={"color_message": color_message})

        # 魔改 —— Start
        self.shutdown_status = True
        # 魔改 —— End
