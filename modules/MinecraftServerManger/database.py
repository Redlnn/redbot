#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from peewee import *
from playhouse.pool import PooledMySQLDatabase, PooledSqliteDatabase
from playhouse.shortcuts import ReconnectMixin

from .config import DatabaseConfig, server_group

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
                        DatabaseConfig.mysql_database,
                        max_connections=5,
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
                        os.path.join(os.getcwd(), 'data', f'MinecraftServerManager_{server_group}.db'),
                        max_connections=5,
                )
            return cls._instance


    db = ReconnectPooledSqliteDatabase.get_db_instance()

if not server_group:
    raise ValueError('server_group is required')


class PlayersTable(Model):
    group = CharField(max_length=12, index=True, column_name='group')
    qq = CharField(max_length=12, index=True, column_name='qq')
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
        table_name = f'redbot_minecraft_players'
        legacy_table_names = False


def init_table():
    db.create_tables([PlayersTable])
