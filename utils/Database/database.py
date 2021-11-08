#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# import os
#
# from peewee import Model
# from peewee_async import PooledMySQLDatabase
# from playhouse.pool import PooledSqliteDatabase
# from playhouse.shortcuts import ReconnectMixin
#
# from config import DatabaseConfig
#
# if DatabaseConfig.mysql:
#     # https://www.cnblogs.com/gcxblogs/p/14969019.html
#     class ReconnectPooledMySQLDatabase(ReconnectMixin, PooledMySQLDatabase):
#
#         _instance = None
#
#         def sequence_exists(self, seq):
#             super().sequence_exists(seq)
#
#         @classmethod
#         def get_db_instance(cls):
#             if not cls._instance:
#                 cls._instance = cls(
#                         DatabaseConfig.database,
#                         max_connections=10,
#                         host=DatabaseConfig.mysql_host,
#                         port=DatabaseConfig.mysql_port,
#                         user=DatabaseConfig.mysql_user,
#                         password=DatabaseConfig.mysql_passwd,
#                 )
#             return cls._instance
#
#
#     db = ReconnectPooledMySQLDatabase.get_db_instance()
# else:
#
#     class ReconnectPooledSqliteDatabase(ReconnectMixin, PooledSqliteDatabase):
#
#         _instance = None
#
#         def sequence_exists(self, seq):
#             super().sequence_exists(seq)
#
#         @classmethod
#         def get_db_instance(cls):
#             if not cls._instance:
#                 cls._instance = cls(
#                         os.path.join(os.getcwd(), 'data', f'{DatabaseConfig.database}.db'),
#                         max_connections=10,
#                 )
#             return cls._instance
#
#
#     db = ReconnectPooledSqliteDatabase.get_db_instance()
#
#
# class BaseModel(Model):
#     class Meta:
#         database = db
