# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

from peewee import Model
from playhouse.pool import PooledMySQLDatabase, PooledSqliteDatabase
from playhouse.shortcuts import ReconnectMixin
from pydantic import BaseModel as PyDanticBaseModel

from utils.config import get_config

__all__ = ['BaseModel', 'database_cfg']


class MySQLConfig(PyDanticBaseModel):
    enabled: bool = False
    host: str = 'localhost'
    port: int = 3306
    user: str = 'user'
    passwd: str = 'password'


class DatabaseConfig(PyDanticBaseModel):
    database: str = 'redbot'
    mysql: MySQLConfig = MySQLConfig()


database_cfg: DatabaseConfig = get_config('database.json', DatabaseConfig())

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
                    Path(Path.cwd(), 'data', f'{database_cfg.database}.db'),
                    max_connections=10,
                )
            return cls._instance

    db = ReconnectPooledSqliteDatabase.get_db_instance()


class BaseModel(Model):
    class Meta:
        database = db
