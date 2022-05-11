#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本模块为示例，仅供参考
"""

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


from .api.overview import (
    get_function_called,
    get_info_card,
    get_message_sent_freq,
    get_siginin_count,
    get_sys_info,
)
from .oauth2 import login_for_access_token
from .oauth2.model import Token
from .response_model import GeneralResponse

fastapicore.asgi.add_api_route('/', endpoint=root, methods=['GET'])  # type: ignore
fastapicore.asgi.add_api_route('/login', endpoint=login_for_access_token, response_model=Token, methods=['POST'])  # type: ignore
fastapicore.asgi.add_api_route('/api/overview/get_info_card', endpoint=get_info_card, response_model=GeneralResponse, methods=['GET'])  # type: ignore
fastapicore.asgi.add_api_route('/api/overview/get_sys_info', endpoint=get_sys_info, response_model=GeneralResponse, methods=['GET'])  # type: ignore
fastapicore.asgi.add_api_route('/api/overview/get_function_called', endpoint=get_function_called, response_model=GeneralResponse, methods=['GET'])  # type: ignore
fastapicore.asgi.add_api_route('/api/overview/get_message_sent_freq', endpoint=get_message_sent_freq, response_model=GeneralResponse, methods=['GET'])  # type: ignore
fastapicore.asgi.add_api_route('/api/overview/get_siginin_count', endpoint=get_siginin_count, response_model=GeneralResponse, methods=['GET'])  # type: ignore

fastapicore.asgi.add_api_websocket_route('/ws', endpoint=websocket)  # type: ignore


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
