#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# from graia.ariadne.app import Ariadne
# from graia.ariadne.event.lifecycle import ApplicationLaunched
# from graia.ariadne.message.chain import MessageChain
# from graia.ariadne.model import Group
# from graia.saya import Channel
# from graia.saya.builtins.broadcast import ListenerSchema
#
# channel = Channel.current()
#
#
# @channel.use(
#         ListenerSchema(
#                 listening_events=[ApplicationLaunched],
#         )
# )
# async def main(app: Ariadne):
#     groups = await app.getGroupList()
#     members = await app.getMemberList(groups[1])
#     # print(await app.getMemberProfile(members[0]))
#     member = await app.getMember(726324810, 731347477)
#     print(member)
