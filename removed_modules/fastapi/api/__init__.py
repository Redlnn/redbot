#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi.responses import ORJSONResponse

from util.fastapi_core.response_model import GeneralResponse
from util.fastapi_core.router import Route as OriginRoute

from .group import get_group_list
from .overview import (
    get_function_called,
    get_info_card,
    get_message_sent_freq,
    get_siginin_count,
    get_sys_info,
)


class Route(OriginRoute):
    kwargs: dict = {'response_class': ORJSONResponse}


routes: list[OriginRoute] = [
    Route(path='/api/get_group_list', endpoint=get_group_list, response_model=GeneralResponse),
    Route(path='/api/overview/get_info_card', endpoint=get_info_card, response_model=GeneralResponse),
    Route(path='/api/overview/get_sys_info', endpoint=get_sys_info, response_model=GeneralResponse),
    Route(path='/api/overview/get_function_called', endpoint=get_function_called, response_model=GeneralResponse),
    Route(path='/api/overview/get_message_sent_freq', endpoint=get_message_sent_freq, response_model=GeneralResponse),
    Route(path='/api/overview/get_siginin_count', endpoint=get_siginin_count, response_model=GeneralResponse),
]
