# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from peewee import CharField, IntegerField, Model, TextField, TimestampField, fn
from playhouse.pool import PooledMySQLDatabase, PooledSqliteDatabase
from playhouse.shortcuts import ReconnectMixin

from ..path import data_path
from .database import database_cfg

__all__ = [
    'MsgLog',
    'log_msg',
    'get_member_talk_count',
    'get_group_talk_count',
    'get_member_last_message',
    'get_group_last_message',
    'get_member_last_message_id',
    'get_group_last_message_id',
    'get_member_last_time',
    'get_group_last_time',
    'get_group_msg_by_id',
    'get_member_msg',
    'get_group_msg',
    'del_member_msg',
    'del_group_msg',
]

if database_cfg.mysql.enabled:
    # https://www.cnblogs.com/gcxblogs/p/14969019.html
    class ReconnectPooledMySQLDatabase(ReconnectMixin, PooledMySQLDatabase):

        _instance = None

        def sequence_exists(self, seq):
            super().sequence_exists(seq)

        @classmethod
        def get_db_instance(cls):
            if not cls._instance:
                cls._instance = cls(
                    database_cfg.database,
                    max_connections=10,
                    host=database_cfg.mysql.host,
                    port=database_cfg.mysql.port,
                    user=database_cfg.mysql.user,
                    password=database_cfg.mysql.passwd,
                )
            return cls._instance

    db = ReconnectPooledMySQLDatabase.get_db_instance()
else:

    class ReconnectPooledSqliteDatabase(ReconnectMixin, PooledSqliteDatabase):

        _instance = None

        def sequence_exists(self, seq):
            super().sequence_exists(seq)

        @classmethod
        def get_db_instance(cls):
            if not cls._instance:
                cls._instance = cls(
                    os.path.join(data_path, f'{database_cfg.database}_msg_history.db'),
                    max_connections=10,
                )
            return cls._instance

    db = ReconnectPooledSqliteDatabase.get_db_instance()


class MsgLog(Model):
    group = CharField(max_length=12, index=True, column_name='group_id')
    qq = CharField(max_length=12, index=True, column_name='qq')
    timestamp = TimestampField(column_name='timestamp')
    msg_id = IntegerField(index=True, column_name='msg_id')
    msg_chain = TextField(column_name='msg_chain')

    class Meta:
        table_name = 'msg_history'
        database = db


db.create_tables([MsgLog])


async def log_msg(group: int | str, qq: int | str, timestamp: int, msg_id: int, msg_chain: str) -> None:
    # 此处的 msg_chain 需要的是 MessageChain().asPersistentString()
    MsgLog.create(group=group, qq=qq, timestamp=timestamp, msg_id=msg_id, msg_chain=msg_chain)


async def get_member_talk_count(group: int | str, qq: int | str, timestamp: int = 0) -> int | None:
    try:
        data = MsgLog.select(fn.Count(MsgLog.msg_id).alias('count')).where(
            (MsgLog.group == group) & (MsgLog.qq == qq) & (MsgLog.timestamp >= timestamp)
        )
    except MsgLog.DoesNotExist:
        return None
    else:
        return data.get().count


async def get_group_talk_count(group: int | str, timestamp: int = 0) -> int | None:
    try:
        data = MsgLog.select(fn.Count(MsgLog.msg_id).alias('count')).where(
            (MsgLog.group == group) & (MsgLog.timestamp >= timestamp)
        )
    except MsgLog.DoesNotExist:
        return None
    else:
        return data.get().count


async def get_member_last_message(group: int | str, qq: int | str) -> tuple[str | None, int | None]:
    try:
        data = MsgLog.select(MsgLog.msg_chain, MsgLog.timestamp).where(
            (MsgLog.group == group)
            & (MsgLog.qq == qq)
            & (
                MsgLog.timestamp
                == MsgLog.select(fn.Max(MsgLog.timestamp)).where((MsgLog.group == group) & (MsgLog.qq == qq))
            )
        )
    except MsgLog.DoesNotExist:
        return None, None
    data_get = data.get()
    return data_get.msg_chain, data_get.timestamp


async def get_group_last_message(group: int | str) -> tuple[str | None, str | None, int | None]:
    try:
        data = MsgLog.select(MsgLog.qq, MsgLog.msg_chain, MsgLog.timestamp).where(
            (MsgLog.group == group)
            & (MsgLog.timestamp == MsgLog.select(fn.Max(MsgLog.timestamp)).where((MsgLog.group == group)))
        )
    except MsgLog.DoesNotExist:
        return None, None, None
    data_get = data.get()
    return data_get.qq, data_get.msg_chain, data_get.timestamp


async def get_member_last_message_id(group: int | str, qq: int | str) -> int | None:
    try:
        data = MsgLog.select(fn.Max(MsgLog.msg_id).alias('last_id')).where((MsgLog.group == group) & (MsgLog.qq == qq))
    except MsgLog.DoesNotExist:
        return None
    return data.get().last_id


async def get_group_last_message_id(group: int | str) -> int | None:
    try:
        data = MsgLog.select(fn.Max(MsgLog.msg_id).alias('last_id')).where(MsgLog.group == group)
    except MsgLog.DoesNotExist:
        return None
    return data.get().last_id


async def get_member_last_time(group: int | str, qq: int | str) -> int | None:
    try:
        data = MsgLog.select(fn.Max(MsgLog.timestamp).alias('last_time')).where(
            (MsgLog.group == group) & (MsgLog.qq == qq)
        )
    except MsgLog.DoesNotExist:
        return None
    return data.get().last_time


async def get_group_last_time(group: int | str) -> int | None:
    try:
        data = MsgLog.select(fn.Max(MsgLog.timestamp).alias('last_time')).where(MsgLog.group == group)
    except MsgLog.DoesNotExist:
        return None
    return data.get().last_time


async def get_group_msg_by_id(group: int | str) -> str | None:
    try:
        data = MsgLog.select(MsgLog.msg_chain).where(MsgLog.group == group)
    except MsgLog.DoesNotExist:
        return None
    return data.get().msg_chain


async def get_member_msg(group: int | str, qq: int | str, timestamp: int = 0) -> list[str]:
    try:
        data = MsgLog.select().where((MsgLog.group == group) & (MsgLog.qq == qq) & (MsgLog.timestamp >= timestamp))
    except MsgLog.DoesNotExist:
        return []
    return [msg.msg_chain for msg in data]


async def get_group_msg(group: int | str, timestamp: int = 0) -> list[str]:
    try:
        data = MsgLog.select().where((MsgLog.group == group) & (MsgLog.timestamp >= timestamp))
    except MsgLog.DoesNotExist:
        return []
    return [msg.msg_chain for msg in data]


async def del_member_msg(group: int | str, qq: int | str, timestamp: int):
    try:
        MsgLog.delete().where((MsgLog.group == group) & (MsgLog.qq == qq) & (MsgLog.timestamp < timestamp)).execute()
    except MsgLog.DoesNotExist:
        pass


async def del_group_msg(group: int | str, timestamp: int):
    try:
        MsgLog.delete().where((MsgLog.group == group) & (MsgLog.timestamp < timestamp)).execute()
    except MsgLog.DoesNotExist:
        pass
