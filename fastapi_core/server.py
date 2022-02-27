#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from uvicorn.server import Server


class NoSignalServer(Server):
    def install_signal_handlers(self) -> None:
        return
