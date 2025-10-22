#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatGPT GUI自動操作 - ログ設定

ログレベルとファイル出力の設定を管理
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class ChatGPTLogger:
    """ChatGPT専用ログ設定クラス"""
    
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    def __init__(self, name: str = 'chatgpt'):
        self.name = name
        self.logger = None
    
    def setup_logger(self, log_file: Optional[str] = None, log_level: str = 'INFO') -> logging.Logger:
        """ログ設定を行い、loggerを返す"""
        
        # ログレベルの検証
        if log_level.upper() not in self.LOG_LEVELS:
            log_level = 'INFO'
        
        level = self.LOG_LEVELS[log_level.upper()]
        
        # ロガー作成（既存があれば再利用）
        logger = logging.getLogger(self.name)
        logger.setLevel(level)
        
        # 既存のハンドラーをクリア（重複防止）
        if logger.handlers:
            logger.handlers.clear()
        
        # フォーマッター
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # ファイルハンドラー（指定がある場合）
        if log_file:
            try:
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.FileHandler(log_path, encoding='utf-8')
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                
            except Exception:
                # ファイルハンドラー作成に失敗した場合は無視
                pass
        
        # コンソールハンドラーは追加しない（既存の出力モードを維持）
        # ログはファイルのみに出力
        
        self.logger = logger
        return logger
    
    def get_logger(self) -> Optional[logging.Logger]:
        """設定済みのloggerを取得"""
        return self.logger


def setup_chatgpt_logger(log_file: Optional[str] = None, log_level: str = 'INFO') -> logging.Logger:
    """ChatGPTロガーを設定（便利関数）"""
    chatgpt_logger = ChatGPTLogger()
    return chatgpt_logger.setup_logger(log_file, log_level)


def get_null_logger() -> logging.Logger:
    """何も出力しないnullロガーを取得"""
    null_logger = logging.getLogger('chatgpt_null')
    null_logger.setLevel(logging.CRITICAL + 1)  # 全てのレベルを無効化
    null_logger.addHandler(logging.NullHandler())
    return null_logger