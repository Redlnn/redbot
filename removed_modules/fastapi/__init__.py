#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from contextvars import ContextVar

from fastapi import WebSocket
from graia.ariadne import get_running
from graia.ariadne.event.lifecycle import ApplicationLaunched, ApplicationShutdowned
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast import Broadcast
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger
from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedOK

from util.fastapi_core import FastApiCore
from util.fastapi_core.event import NewWebsocketClient
from util.fastapi_core.manager import WsConnectionManager
from util.fastapi_core.router import Router

channel = Channel.current()
manager = WsConnectionManager()
fastapicore = FastApiCore(listen_host='0.0.0.0')
broadcast: ContextVar[Broadcast] = ContextVar('bcc')


async def root():
    return {'message': 'Hello World'}


async def websocket(client: WebSocket):
    await manager.connect(client)
    bcc = broadcast.get(None)
    if bcc is None:
        return
    bcc.postEvent(NewWebsocketClient(client))
    while True:
        try:
            data = await client.receive_text()
            logger.info(f'websockets recived: {data}')
        except (WebSocketDisconnect, ConnectionClosedOK):
            manager.disconnect(client)
        except RuntimeError:
            break


from .oauth2 import login_for_access_token
from .oauth2.model import Token

fastapicore.asgi.add_api_route('/', endpoint=root, methods=['GET'])  # type: ignore
fastapicore.asgi.add_api_route('/login', endpoint=login_for_access_token, response_model=Token, methods=['POST'])  # type: ignore

fastapicore.asgi.add_api_websocket_route('/ws', endpoint=websocket)

import importlib
import os

for i in os.listdir(os.path.join('api')):
    if i.endswith('.py'):
        importlib.import_module(f'api.{i[:-3]}')
    else:
        importlib.import_module(f'api.{i}')


for i in Router.routes:
    fastapicore.asgi.add_api_route(i.path, endpoint=i.endpoint, response_model=i.response_model, methods=i.methods)


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def on_launch():
    broadcast.set(get_running(Broadcast))
    await fastapicore.start()


@channel.use(ListenerSchema(listening_events=[ApplicationShutdowned]))
async def on_shutdown():
    await fastapicore.stop()


@channel.use(ListenerSchema(listening_events=[NewWebsocketClient]))
async def new_websocket_client(client: WebSocket):
    await client.send_text(f'Hello Broadcast')


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def on_msg(message: MessageChain):
    await manager.broadcast(message.asDisplay())
