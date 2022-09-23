#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

root_path: Path = Path(__file__).parent.parent.resolve()
config_path: Path = Path(root_path, 'config')
logs_path: Path = Path(root_path, 'logs')
modules_path: Path = Path(root_path, 'modules')
data_path: Path = Path(root_path, 'data')
lib_path: Path = Path(root_path, 'libs')

config_path.mkdir(parents=True, exist_ok=True)
logs_path.mkdir(parents=True, exist_ok=True)
modules_path.mkdir(parents=True, exist_ok=True)
data_path.mkdir(parents=True, exist_ok=True)
lib_path.mkdir(parents=True, exist_ok=True)
