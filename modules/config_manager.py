#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Manager for LINE Stamp Maker
"""

import json
from pathlib import Path
from typing import Any, Dict


class ConfigManager:
    """設定管理クラス"""

    DEFAULT_CONFIG = {
        "settings": {
            "resize_mode": "fit",
            "output_base_path": "C:\\LINE_OUTPUTS",
            "auto_skip_png": True,
            "max_stamp_count": 40
        },
        "paths": {
            "line_stamp_maker": "./line_stamp_maker",
            "auto_prompter": "./AutoPrompter/launch-chatgpt-prefix.bat",
            "node_executable": "node"
        },
        "resize": {
            "fit": {"width": 370, "height": 320},
            "trim": {"width": 370, "height": 320},
            "main": {"width": 240, "height": 240},
            "tab": {"width": 96, "height": 74}
        },
        "logging": {
            "enabled": True,
            "log_folder": "./logs",
            "max_log_files": 30
        }
    }

    def __init__(self, config_path='./config.json'):
        self.config_path = Path(config_path)
        self.config = None
        self.load()

    def load(self):
        """設定ファイルを読み込み"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            self.config = self.DEFAULT_CONFIG.copy()
            self.save()

    def save(self):
        """設定ファイルを保存"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error: Failed to save config: {e}")

    def get(self, key_path: str, default=None) -> Any:
        """
        ドット区切りのキーパスで設定値を取得
        例: get('settings.resize_mode')
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """
        ドット区切りのキーパスで設定値を設定
        例: set('settings.resize_mode', 'trim')
        """
        keys = key_path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def get_all(self) -> Dict:
        """すべての設定を取得"""
        return self.config.copy()

    def update(self, updates: Dict):
        """設定を一括更新"""
        def recursive_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict) and k in d:
                    recursive_update(d[k], v)
                else:
                    d[k] = v

        recursive_update(self.config, updates)
        self.save()
