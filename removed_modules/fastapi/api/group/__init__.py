#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from contextvars import ContextVar

from graia.ariadne import get_running
from graia.ariadne.app import Ariadne
from graia.ariadne.model import MemberPerm

from util.fastapi_core.response_model import GeneralResponse
from util.fastapi_core.router import Router

perm_map = {
    MemberPerm.Member: '群成语',
    MemberPerm.Administrator: '管理员',
    MemberPerm.Owner: '群主',
}

group_list_cache: ContextVar[dict[int, str | int]] = ContextVar('group_list_cache')
last_get_group_list_time: ContextVar[float] = ContextVar('last_get_group_list_time')


@Router.get('/api/get_group_list', response_model=GeneralResponse)
async def get_group_list():
    last = last_get_group_list_time.get(None)
    if last is not None and (time.time() - last) < 120:
        tmp = group_list_cache.get(None)
        if tmp is not None:
            return GeneralResponse(data=tmp)

    last_get_group_list_time.set(time.time())

    app = get_running(Ariadne)
    group_list = await app.getGroupList()
    tmp = {
        group.id: {
            'id': group.id,
            'name': group.name,
            'accountPerm': perm_map[group.accountPerm],
        }
        for group in group_list
    }

    group_list_cache.set(tmp)
    return GeneralResponse(data=tmp)
