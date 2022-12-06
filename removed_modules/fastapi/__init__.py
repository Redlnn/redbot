from creart import create
from fastapi import FastAPI, WebSocket
from graia.amnesia.transport.common.asgi import ASGIHandlerProvider
from graia.ariadne.app import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast import Broadcast
from graia.saya import Channel
from graiax.shortcut.saya import listen
from loguru import logger
from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedOK

from util.fastapi_service.event import NewWebsocketClient
from util.fastapi_service.manager import WsConnectionManager

from .oauth2 import Token, login_for_access_token

channel = Channel.current()

channel.meta['name'] = 'API'
channel.meta['author'] = ['Red_lnn']
channel.meta['can_disable'] = False

manager = WsConnectionManager()


async def root():
    return {'message': 'Hello World'}


async def websocket(client: WebSocket):
    await manager.connect(client)
    bcc = create(Broadcast)
    bcc.postEvent(NewWebsocketClient(client))
    while True:
        try:
            data = await client.receive_text()
            logger.info(f'websockets received: {data}')
        except (WebSocketDisconnect, ConnectionClosedOK, RuntimeError):
            manager.disconnect(client)
            break


# @listen(ApplicationLaunched)
# async def init(app: Ariadne, asgi_handler: ASGIHandlerProvider):
#     mgr = app.launch_manager
#     asgi: FastAPI = asgi_handler.get_asgi_handler()  # type: ignore

#     asgi.add_api_route('/', endpoint=root, methods=['GET'])  # type: ignore
#     asgi.add_api_route(
#         '/login', endpoint=login_for_access_token, response_model=Token, methods=['POST']  # type: ignore
#     )

#     asgi.add_api_websocket_route('/ws', endpoint=websocket)

#     for route in routes:
#         asgi.add_api_route(
#             path=route.path,
#             methods=route.methods,
#             endpoint=route.endpoint,
#             response_model=route.response_model,
#             **route.kwargs,
#         )

#     for route in Router.routes:
#         asgi.add_api_route(
#             path=route.path,
#             methods=route.methods,
#             endpoint=route.endpoint,
#             response_model=route.response_model,
#             **route.kwargs,
#         )


@listen(NewWebsocketClient)
async def new_websocket_client(client: WebSocket):
    await client.send_text('Hello Broadcast')


@listen(GroupMessage)
async def on_msg(message: MessageChain):
    await manager.broadcast(str(message))
