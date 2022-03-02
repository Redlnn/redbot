#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

from sqlalchemy.types import *
from sqlmodel import Column, Field, SQLModel


class PlayerInfo(SQLModel, table=True):
    __tablename__: str = 'minecraft_player_info'
    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    qq: str = Field(max_length=12, nullable=False, index=True)
    join_time: Optional[int] = Field(default=None, nullable=True)
    leave_time: Optional[int] = Field(default=None, nullable=True)
    uuid1: Optional[str] = Field(
        sa_column=Column(VARCHAR(32), index=True, nullable=True, default=None), nullable=True, default=None
    )
    uuid1_add_time: Optional[int] = Field(default=None, nullable=True)
    uuid2: Optional[str] = Field(
        sa_column=Column(VARCHAR(32), index=True, nullable=True, default=None), nullable=True, default=None
    )
    uuid2_add_time: Optional[int] = Field(default=None, nullable=True)
    blocked: bool = Field(default=False)
    block_reason: Optional[str] = Field(default=None, nullable=True)
