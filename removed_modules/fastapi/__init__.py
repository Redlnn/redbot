#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本模块为示例，仅供参考
"""

import asyncio
from asyncio import Task

from fastapi import FastAPI, WebSocket
from graia.ariadne.app import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunched, ApplicationShutdowned
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast import Broadcast
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger
from starlette.websockets import WebSocketDisconnect
from uvicorn.config import Config
from websockets.exceptions import ConnectionClosedOK

from fastapi_core.event import NewWebsocketClient
from fastapi_core.manager import ConnectionManager
from fastapi_core.server import ModifiedServer as Server
from util.logger_rewrite import rewrite_logging_logger

rewrite_logging_logger('uvicorn.error')
rewrite_logging_logger('uvicorn.access')
rewrite_logging_logger('uvicorn.asgi')

task: Task
channel = Channel.current()
bcc = Ariadne.get_running(Broadcast)
fastapi_app = FastAPI()
manager = ConnectionManager()


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def on_launch():
    global task
    server = Server(Config(fastapi_app, host='localhost', port=18000, log_config=None, reload=False))
    task = asyncio.create_task(server.serve())


@channel.use(ListenerSchema(listening_events=[ApplicationShutdowned]))
async def on_shutdown():
    task.cancel()


@channel.use(ListenerSchema(listening_events=[NewWebsocketClient]))
async def new_websocket_client(client: WebSocket):
    await client.send_text(f'Hello Broadcast')


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def on_msg(message: MessageChain):
    await manager.broadcast(message.asDisplay())


@fastapi_app.get('/')
async def root():
    return {'message': 'Hello World'}


@fastapi_app.websocket('/ws')
async def websocket(client: WebSocket):
    await manager.connect(client)
    bcc.postEvent(NewWebsocketClient(client))
    while True:
        try:
            data = await client.receive_text()
            logger.info(f'websockets recived: {data}')
        except (WebSocketDisconnect, ConnectionClosedOK):
            manager.disconnect(client)
        except RuntimeError:
            break
