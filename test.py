#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import uuid
from typing import Type, TypeVar

from peewee import *

from utils.Database.database import BaseModel, db

from utils.logger import logger


class Users(BaseModel):
    qq = CharField(max_length=12, unique=True, column_name='qq')
    joinTimestamp = TimestampField(column_name='joinTimestamp')
    uuid1 = UUIDField(index=True, null=True, column_name='uuid1')
    uuid2 = UUIDField(index=True, null=True, column_name='uuid2')
    blocked = BooleanField(default=False, column_name='blocked')
    blockReason = TextField(null=True, column_name='blockReason')

    class Meta:
        legacy_table_names = False


T_Users = TypeVar('T_Users', bound=Users)


def get_group_users_db(group: int) -> Type[T_Users]:
    class GroupUsers(Users):
        class Meta:
            table_name = f'users_{group}'

    return GroupUsers


b = get_group_users_db(726324810)

# db.create_tables([b])

# data = (b.update({b.uuid1: None}).where(b.qq == 731347477))
# data.execute()
# data = b(qq=731347477)
# data.save()
try:
    data = b.get((b.qq == 731347477))
    print(str(data.uuid1))
except b.DoesNotExist:
    pass
