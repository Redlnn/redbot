#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import WebSocketDisconnect
from fastapi.websockets import WebSocket
from websockets.exceptions import ConnectionClosedOK


class WsConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except (WebSocketDisconnect, ConnectionClosedOK):
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except (WebSocketDisconnect, ConnectionClosedOK):
                self.disconnect(connection)
