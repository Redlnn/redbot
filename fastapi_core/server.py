#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import signal
import threading

from uvicorn.server import Server

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)


class ModifiedServer(Server):
    def install_signal_handlers(self) -> None:
        if threading.current_thread() is not threading.main_thread():
            # Signals can only be listened to from the main thread.
            return

        loop = asyncio.get_event_loop()

        try:
            for sig in HANDLED_SIGNALS:
                loop.add_signal_handler(sig, self.handle_exit, sig, None)
        except NotImplementedError:  # pragma: no cover
            # Windows
            for sig in HANDLED_SIGNALS:
                handler = signal.getsignal(sig)

                def handler_wrapper(sig_num, frame):
                    self.handle_exit(sig_num, frame)
                    if handler:
                        handler(sig_num, frame)

                signal.signal(sig, handler_wrapper)
