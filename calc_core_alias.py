# -*- coding: utf-8 -*-
"""
ASCII 入口包装：加载同目录下的“盈利计算.py”，并导出核心对象，便于 Android 打包时避免非 ASCII 模块名的导入问题。
"""
from __future__ import annotations

import importlib.util
import sys
from types import ModuleType

_MOD_NAME = "calc_core_loaded"
_FILE = "盈利计算.py"

spec = importlib.util.spec_from_file_location(_MOD_NAME, _FILE)
if spec is None or spec.loader is None:
    raise ImportError(f"无法加载模块文件：{_FILE}")
_mod = importlib.util.module_from_spec(spec)
sys.modules[_MOD_NAME] = _mod
spec.loader.exec_module(_mod)  # type: ignore

# re-exports
PositionPlan = _mod.PositionPlan
LumpExit = _mod.LumpExit
GridExit = _mod.GridExit
compute_schedule_pnl_core = _mod.compute_schedule_pnl_core
pv = _mod.pv

