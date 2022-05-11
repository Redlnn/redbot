#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""unused"""

import platform

import psutil

from util.better_pydantic import BaseModel

uname = platform.uname()


class SysInfo(BaseModel):
    system_type: str = uname.system
    system_release: str = uname.release
    system_version: str = uname.version
    cpu_logical_count: int = psutil.cpu_count(logical=True)
    cpu_physical_count: int = psutil.cpu_count(logical=False)
    cpu_percent: float
    memory_total: int = psutil.virtual_memory().total  # Byte
    memory_used: int
    memory_available: int
    memory_percent: float
    disk_percent: float
    uptime: float


class RunningTime(BaseModel):
    duration: str
    unit: str


class InfoCard(BaseModel):
    today_msg_count: int
    function_called_count: int
    joined_group_count: int
    module_loaded_count: int
    running_time: RunningTime


class FunctionCalled(BaseModel):
    function_name: str
    function_called_count: int


class TotalFunctionCalled(BaseModel):
    called: list[FunctionCalled]
