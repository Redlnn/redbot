#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

from peewee import BooleanField, CharField, Model, TextField, TimestampField, UUIDField
from playhouse.pool import PooledMySQLDatabase, PooledSqliteDatabase
from playhouse.shortcuts import ReconnectMixin

from util.path import data_path

from .config import config

if config.database.enableMySQL:
    # https://www.cnblogs.com/gcxblogs/p/14969019.html
    class ReconnectPooledMySQLDatabase(ReconnectMixin, PooledMySQLDatabase):

        _instance = None

        def sequence_exists(self, seq):
            super().sequence_exists(seq)

        @classmethod
        def get_db_instance(cls):
            if not cls._instance:
                cls._instance = cls(
                    config.database.database,
                    max_connections=5,
                    host=config.database.host,
                    port=config.database.port,
                    user=config.database.user,
                    password=config.database.passwd,
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
                    Path(data_path, f'MinecraftServerManager_{config.serverGroup}.db'),
                    max_connections=5,
                )
            return cls._instance

    db = ReconnectPooledSqliteDatabase.get_db_instance()


class PlayersTable(Model):
    group = CharField(max_length=12, index=True, column_name='sourceGroup')
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
        table_name = 'redbot_minecraft_players'
        legacy_table_names = False


def init_table():
    db.create_tables([PlayersTable])
