#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Type, TypeVar

from peewee import *
from peewee_async import PooledMySQLDatabase
from playhouse.pool import PooledSqliteDatabase
from playhouse.shortcuts import ReconnectMixin

from .config import DatabaseConfig

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
                        os.path.join(os.getcwd(), 'data', f'{DatabaseConfig.database}.db'),
                        max_connections=10,
                )
            return cls._instance


    db = ReconnectPooledSqliteDatabase.get_db_instance()


class PlayersListTable(Model):
    qq = CharField(max_length=12, unique=True, column_name='qq')
    joinTimestamp = TimestampField(column_name='joinTimestamp')
    leaveTimestamp = TimestampField(null=True, default=None, column_name='leaveTimestamp')
    uuid1 = UUIDField(index=True, null=True, default=None, column_name='uuid1')
    uuid1AddedTime = TimestampField(null=True, default=None, column_name='uuid1AddedTime')
    uuid2 = UUIDField(index=True, null=True, default=None, column_name='uuid2')
    uuid2AddedTime = TimestampField(null=True, default=None, column_name='uuid2AddedTime')
    blocked = BooleanField(default=False, column_name='blocked')
    blockReason = TextField(null=True, default=None, column_name='blockReason')

    class Meta:
        database = db
        legacy_table_names = False


T_PlayersListTable = TypeVar('T_PlayersListTable', bound=PlayersListTable)
T_PlayersListTable = Type[T_PlayersListTable]


def get_group_players_list_table(group: int) -> T_PlayersListTable:
    class GroupPlayersListTable(PlayersListTable):
        class Meta:
            table_name = f'players_{group}'

    return GroupPlayersListTable


def init_group_players_list_table(group: int):
    class GroupPlayersListTable(PlayersListTable):
        class Meta:
            table_name = f'players_{group}'

    db.create_tables([GroupPlayersListTable])
