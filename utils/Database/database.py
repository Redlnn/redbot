# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from peewee import Model
from playhouse.pool import PooledMySQLDatabase, PooledSqliteDatabase
from playhouse.shortcuts import ReconnectMixin

from config import config_data

if config_data['Basic']['Database']['MySQL']:
    # https://www.cnblogs.com/gcxblogs/p/14969019.html
    class ReconnectPooledMySQLDatabase(ReconnectMixin, PooledMySQLDatabase):

        _instance = None

        def sequence_exists(self, seq):
            super().sequence_exists(seq)

        @classmethod
        def get_db_instance(cls):
            if not cls._instance:
                cls._instance = cls(
                        config_data['Basic']['Database']['Database'],
                        max_connections=10,
                        host=config_data['Basic']['Database']['Host'],
                        port=config_data['Basic']['Database']['Port'],
                        user=config_data['Basic']['Database']['User'],
                        password=config_data['Basic']['Database']['Passwd'],
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
                        os.path.join(os.getcwd(), 'data', f'{config_data["Basic"]["Database"]["Database"]}.db'),
                        max_connections=10,
                )
            return cls._instance

    db = ReconnectPooledSqliteDatabase.get_db_instance()


class BaseModel(Model):
    class Meta:
        database = db
