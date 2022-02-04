#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class Player(BaseModel):
    group: int
    qq: int
    joinTime: datetime
    leaveTime: datetime | None = None
    uuid1: UUID | None = None
    uuid1AddedTime: datetime | None = None
    uuid2: UUID | None = None
    uuid2AddedTime: datetime | None = None
    blocked: bool = False
    blockReason: str | None = None
