#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatGPT GUI自動操作 - 設定管理

CLI > ENV > config ファイルの優先順位で設定をマージする
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import argparse


class ChatGPTConfig:
    """設定管理クラス"""
    
    # デフォルト設定値
    DEFAULTS = {
        'csv': None,
        'wait': 60,
        'profile_dir': None,
        'pause_for_login': False,
        'output_mode': 'verbose',
        'interactive': False,
        'quiet': False,
        'log_file': None,
        'log_level': 'INFO',
        'dry_run': False,
        'max_items': None,
        'retry': 0,
        'prefix': '',
        'suffix': '',
        'short_sleep': None,
        'long_sleep': None,
        'use_csv_mode': False
    }
    
    # 環境変数のマッピング
    ENV_MAPPING = {
        'CHATGPT_CSV': 'csv',
        'CHATGPT_WAIT': 'wait',
        'CHATGPT_PROFILE_DIR': 'profile_dir',
        'CHATGPT_PAUSE_FOR_LOGIN': 'pause_for_login',
        'CHATGPT_OUTPUT_MODE': 'output_mode',
        'CHATGPT_INTERACTIVE': 'interactive',
        'CHATGPT_QUIET': 'quiet',
        'CHATGPT_LOG_FILE': 'log_file',
        'CHATGPT_LOG_LEVEL': 'log_level',
        'CHATGPT_DRY_RUN': 'dry_run',
        'CHATGPT_MAX_ITEMS': 'max_items',
        'CHATGPT_RETRY': 'retry',
        'CHATGPT_PREFIX': 'prefix',
        'CHATGPT_SUFFIX': 'suffix'
    }
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self._config = {}
    
    def load_config_file(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        if not self.config_file:
            return {}
        
        config_path = Path(self.config_file)
        if not config_path.exists():
            return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            # YAML構造を平坦化 (chatgpt.csv -> csv)
            config = {}
            if 'chatgpt' in data:
                config.update(data['chatgpt'])
            if 'output' in data:
                for key, value in data['output'].items():
                    if key == 'mode':
                        config['output_mode'] = value
                    else:
                        config[key] = value
            if 'logging' in data:
                for key, value in data['logging'].items():
                    config[key] = value
            if 'safety' in data:
                for key, value in data['safety'].items():
                    config[key] = value
            
            return config
            
        except Exception:
            return {}
    
    def load_env_vars(self) -> Dict[str, Any]:
        """環境変数を読み込み"""
        env_config = {}
        
        for env_key, config_key in self.ENV_MAPPING.items():
            value = os.getenv(env_key)
            if value is not None:
                # 型変換
                if config_key in ['wait', 'max_items', 'retry']:
                    try:
                        env_config[config_key] = int(value)
                    except ValueError:
                        continue
                elif config_key in ['pause_for_login', 'interactive', 'quiet', 'dry_run']:
                    env_config[config_key] = value.lower() in ('true', '1', 'yes', 'on')
                else:
                    env_config[config_key] = value
        
        return env_config
    
    def merge_configs(self, cli_args: argparse.Namespace) -> Dict[str, Any]:
        """CLI > ENV > config の優先順位で設定をマージ"""
        
        # 1. デフォルト値から開始
        merged = self.DEFAULTS.copy()
        
        # 2. 設定ファイルの値で上書き
        file_config = self.load_config_file()
        merged.update(file_config)
        
        # 3. 環境変数で上書き
        env_config = self.load_env_vars()
        merged.update(env_config)
        
        # 4. CLI引数で最終上書き（None以外の値のみ）
        cli_config = {}
        
        # CLI引数のマッピング（明示的に指定された値のみ）
        cli_mapping = {
            'csv': cli_args.csv,
            'wait': cli_args.wait,
            'profile_dir': getattr(cli_args, 'profile_dir', None),
            'pause_for_login': getattr(cli_args, 'pause_for_login', None),
            'log_file': getattr(cli_args, 'log_file', None),
            'log_level': getattr(cli_args, 'log_level', None),
            'prefix': getattr(cli_args, 'prefix', ''),
            'suffix': getattr(cli_args, 'suffix', '')
        }

        # boolean引数は明示的に指定された場合のみ上書き
        if getattr(cli_args, 'dry_run', False):
            cli_mapping['dry_run'] = True

        if getattr(cli_args, 'csv_mode', False):
            cli_mapping['use_csv_mode'] = True

        # 数値引数も明示的にチェック
        if hasattr(cli_args, 'max_items') and cli_args.max_items is not None:
            cli_mapping['max_items'] = cli_args.max_items

        if hasattr(cli_args, 'retry') and cli_args.retry != 0:  # デフォルト以外の値
            cli_mapping['retry'] = cli_args.retry

        if hasattr(cli_args, 'short_sleep') and cli_args.short_sleep is not None:
            cli_mapping['short_sleep'] = cli_args.short_sleep

        if hasattr(cli_args, 'long_sleep') and cli_args.long_sleep is not None:
            cli_mapping['long_sleep'] = cli_args.long_sleep
        
        # 出力モード判定
        if getattr(cli_args, 'json', False):
            cli_config['output_mode'] = 'json'
        elif getattr(cli_args, 'ndjson', False):
            cli_config['output_mode'] = 'ndjson'
        elif getattr(cli_args, 'quiet', False):
            cli_config['output_mode'] = 'quiet'
        elif getattr(cli_args, 'verbose', False):
            cli_config['output_mode'] = 'verbose'
        
        # interactive フラグ
        if getattr(cli_args, 'interactive', False):
            cli_config['interactive'] = True
        
        # None以外の値のみ採用
        for key, value in cli_mapping.items():
            if value is not None:
                cli_config[key] = value
        
        merged.update(cli_config)
        
        # 結果を保存
        self._config = merged
        return merged
    
    def get(self, key: str, default=None):
        """設定値を取得"""
        return self._config.get(key, default)
    
    def __getitem__(self, key: str):
        return self._config[key]
    
    def __contains__(self, key: str):
        return key in self._config
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書として取得"""
        return self._config.copy()


def create_config(config_file: Optional[str] = None, cli_args: Optional[argparse.Namespace] = None) -> ChatGPTConfig:
    """設定オブジェクトを作成"""
    config = ChatGPTConfig(config_file)
    if cli_args:
        config.merge_configs(cli_args)
    return config