#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional
from uuid import UUID

from sqlmodel import Field, SQLModel


class PlayerInfo(SQLModel, table=True):
    __tablename__: str = 'minecraft_player_info'
    qq: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    join_time: int
    leave_time: Optional[int] = Field(default=None, nullable=True)
    uuid1: Optional[UUID] = Field(default=None, nullable=True, index=True)
    uuid1_add_time: Optional[int] = Field(default=None, nullable=True)
    uuid2: Optional[UUID] = Field(default=None, nullable=True, index=True)
    uuid2_add_time: Optional[int] = Field(default=None, nullable=True)
    blocked: bool = Field(default=False)
    block_reason: Optional[str] = Field(default=None, nullable=True)


# class Player(BaseModel):
#     group: int
#     qq: int
#     joinTime: datetime
#     leaveTime: datetime | None = None
#     uuid1: UUID | None = None
#     uuid1AddedTime: datetime | None = None
#     uuid2: UUID | None = None
#     uuid2AddedTime: datetime | None = None
#     blocked: bool = False
#     blockReason: str | None = None
