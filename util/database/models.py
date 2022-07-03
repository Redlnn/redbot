#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import Column
from sqlalchemy.types import TEXT
from sqlmodel import Field, SQLModel

__all__ = ['MsgLog', 'UserInfo']


class MsgLog(SQLModel, table=True):
    __tablename__: str = 'msg_history'
    id: int | None = Field(default=None, primary_key=True, nullable=False)
    group_id: str = Field(max_length=12, nullable=False, index=True)
    member_id: str = Field(max_length=12, nullable=False, index=True)
    timestamp: int
    msg_id: int
    msg_chain: str = Field(sa_column=Column(TEXT, nullable=False), nullable=False)


class UserInfo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, nullable=False)
    qq: str = Field(max_length=12, nullable=False, index=True)
    exp: int = Field(default=0)
    coin: int = Field(default=0)
    gold: int = Field(default=0)
    total_signin_days: int = Field(default=0)
    consecutive_signin_days: int = Field(default=0)
    last_signin_time: int = Field(default=0)
