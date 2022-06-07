#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi.websockets import WebSocket
from graia.broadcast import BaseDispatcher, Dispatchable
from graia.broadcast.interfaces.dispatcher import DispatcherInterface


class NewWebsocketClient(Dispatchable):
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    class Dispatcher(BaseDispatcher):
        @staticmethod
        async def catch(interface: DispatcherInterface['NewWebsocketClient']):
            if isinstance(interface.event, NewWebsocketClient) and interface.annotation is WebSocket:
                return interface.event.websocket
