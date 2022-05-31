#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from contextvars import ContextVar

from graia.ariadne.app import Ariadne
from graia.ariadne.model import MemberPerm

from util.fastapi_core.response_model import GeneralResponse
from util.fastapi_core.router import Router

perm_map = {
    MemberPerm.Member: '群成语',
    MemberPerm.Administrator: '管理员',
    MemberPerm.Owner: '群主',
}


@Router.get('/api/get_group_list', response_model=GeneralResponse)
async def get_group_list():
    app = Ariadne.current()
    group_list = await app.get_groupList()

    tmp: dict[int, dict[str, int | str]] = {
        group.id: {
            'id': group.id,
            'name': group.name,
            'accountPerm': perm_map[group.accountPerm],
        }
        for group in group_list
    }

    return GeneralResponse(data=tmp)
