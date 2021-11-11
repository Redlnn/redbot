# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Optional

from peewee import CharField, fn, IntegerField, Model, TextField, TimestampField
from playhouse.pool import PooledMySQLDatabase, PooledSqliteDatabase
from playhouse.shortcuts import ReconnectMixin

from config import DatabaseConfig

if DatabaseConfig.mysql:
    # https://www.cnblogs.com/gcxblogs/p/14969019.html
    class ReconnectPooledMySQLDatabase(ReconnectMixin, PooledMySQLDatabase):

        _instance = None

        def sequence_exists(self, seq):
            super().sequence_exists(seq)

        @classmethod
        def get_db_instance(cls):
            if not cls._instance:
                cls._instance = cls(
                        DatabaseConfig.database,
                        max_connections=10,
                        host=DatabaseConfig.mysql_host,
                        port=DatabaseConfig.mysql_port,
                        user=DatabaseConfig.mysql_user,
                        password=DatabaseConfig.mysql_passwd,
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
                        os.path.join(os.getcwd(), 'data', f'{DatabaseConfig.database}_msg_history.db'),
                        max_connections=10,
                )
            return cls._instance


    db = ReconnectPooledSqliteDatabase.get_db_instance()


class MsgLog(Model):
    group = CharField(max_length=12, index=True, column_name='group')
    qq = CharField(max_length=12, index=True, column_name='qq')
    timestamp = TimestampField(column_name='timestamp')
    msg_id = IntegerField(unique=True, column_name='msg_id')
    msg_chain = TextField(column_name='msg_chain')

    class Meta:
        table_name = 'msg_history'
        database = db


db.create_tables([MsgLog])


async def log_msg(group: int | str, qq: int | str, timestamp: int, msg_id: int, msg_chain: str) -> None:
    # 此处的 msg_chain 需要的是 MessageChain().asPersistentString()
    MsgLog.create(group=group, qq=qq, timestamp=timestamp, msg_id=msg_id, msg_chain=msg_chain)


async def get_member_talk_count(group: int | str, qq: int | str, timestamp: int = 0) -> Optional[int]:
    try:
        data = MsgLog.select(fn.Count(MsgLog.msg_id).alias('count')).where(
                (MsgLog.group == group) & (MsgLog.qq == qq) & (MsgLog.timestamp >= timestamp)
        )
    except MsgLog.DoesNotExist:
        return None
    else:
        return data.get().count


async def get_group_talk_count(group: int | str, timestamp: int = 0) -> Optional[int]:
    try:
        data = MsgLog.select(fn.Count(MsgLog.msg_id).alias('count')).where(
                (MsgLog.group == group) & (MsgLog.timestamp >= timestamp)
        )
    except MsgLog.DoesNotExist:
        return None
    else:
        return data.get().count


async def get_member_last_message(group: int | str, qq: int | str) -> Optional[str]:
    try:
        data = MsgLog.select(MsgLog.msg_chain).where((MsgLog.group == group) & (MsgLog.qq == qq))
    except MsgLog.DoesNotExist:
        return None
    return data.get().msg_chain


async def get_group_last_message(group: int | str) -> Optional[str]:
    try:
        data = MsgLog.select(MsgLog.msg_chain).where(MsgLog.group == group)
    except MsgLog.DoesNotExist:
        return None
    return data.get().msg_chain


async def get_member_last_message_id(group: int | str, qq: int | str) -> Optional[int]:
    try:
        data = MsgLog.select(fn.Max(MsgLog.msg_id).alias('last_id')).where((MsgLog.group == group) & (MsgLog.qq == qq))
    except MsgLog.DoesNotExist:
        return None
    return data.get().last_id


async def get_group_last_message_id(group: int | str) -> Optional[int]:
    try:
        data = MsgLog.select(fn.Max(MsgLog.msg_id).alias('last_id')).where(MsgLog.group == group)
    except MsgLog.DoesNotExist:
        return None
    return data.get().last_id


async def get_member_last_time(group: int | str, qq: int | str) -> Optional[int]:
    try:
        data = MsgLog.select(fn.Max(MsgLog.timestamp).alias('last_time')).where(
                (MsgLog.group == group) & (MsgLog.qq == qq)
        )
    except MsgLog.DoesNotExist:
        return None
    return data.get().last_time


async def get_group_last_time(group: int | str) -> Optional[int]:
    try:
        data = MsgLog.select(fn.Max(MsgLog.timestamp).alias('last_time')).where(MsgLog.group == group)
    except MsgLog.DoesNotExist:
        return None
    return data.get().last_time


async def get_group_msg_by_id(group: int | str) -> Optional[str]:
    try:
        data = MsgLog.select(MsgLog.msg_chain).where(MsgLog.group == group)
    except MsgLog.DoesNotExist:
        return None
    return data.get().msg_chain


async def get_member_msg(group: int | str, qq: int | str, timestamp: int = 0) -> Optional[list]:
    try:
        data = MsgLog.select().where((MsgLog.group == group) & (MsgLog.qq == qq) & (MsgLog.timestamp >= timestamp))
    except MsgLog.DoesNotExist:
        return None
    return [msg.msg_chain for msg in data]


async def get_group_msg(group: int | str, timestamp: int = 0) -> Optional[list]:
    try:
        data = MsgLog.select().where((MsgLog.group == group) & (MsgLog.timestamp >= timestamp))
    except MsgLog.DoesNotExist:
        return None
    return [msg.msg_chain for msg in data]


async def del_member_msg(group: int | str, qq: int | str, timestamp: int):
    try:
        MsgLog.delete().where((MsgLog.group == group) & (MsgLog.qq == qq) & (MsgLog.timestamp <= timestamp)).execute()
    except MsgLog.DoesNotExist:
        pass


async def del_group_msg(group: int | str, timestamp: int):
    try:
        MsgLog.delete().where((MsgLog.group == group) & (MsgLog.timestamp <= timestamp)).execute()
    except MsgLog.DoesNotExist:
        pass
