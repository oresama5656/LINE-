#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatGPT GUI自動操作モジュール

イベント駆動アーキテクチャ対応版
- 完全なUI/コア分離
- Generator パターンでの進捗通知
- 複数出力モード対応 (JSON/NDJSON/Verbose/Interactive/Quiet)
"""

from .chatgpt_core import iter_process_prompts, InputError, RunError

__version__ = "1.1.0"
__all__ = ["iter_process_prompts", "InputError", "RunError"]