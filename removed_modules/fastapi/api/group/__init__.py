#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from graia.ariadne.app import Ariadne
from graia.ariadne.model import MemberPerm

from util.fastapi_service.response_model import GeneralResponse

perm_map = {
    MemberPerm.Member: '群成语',
    MemberPerm.Administrator: '管理员',
    MemberPerm.Owner: '群主',
}


async def get_group_list():
    app = Ariadne.current()
    group_list = await app.get_group_list()

    tmp: dict[int, dict[str, int | str]] = {
        group.id: {
            'id': group.id,
            'name': group.name,
            'accountPerm': perm_map[group.account_perm],
        }
        for group in group_list
    }

    return GeneralResponse(data=tmp)
