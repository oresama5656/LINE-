#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logger module for LINE Stamp Maker
"""

import logging
import os
from datetime import datetime
from pathlib import Path


class StampMakerLogger:
    """ログ管理クラス"""

    def __init__(self, log_folder='./logs', max_log_files=30):
        self.log_folder = Path(log_folder)
        self.max_log_files = max_log_files
        self.logger = None

    def setup(self):
        """ロガーのセットアップ"""
        # ログフォルダ作成
        self.log_folder.mkdir(parents=True, exist_ok=True)

        # 古いログファイル削除
        self._cleanup_old_logs()

        # ログファイル名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.log_folder / f'stamp_maker_{timestamp}.log'

        # ロガー設定
        logger = logging.getLogger('stamp_maker')
        logger.setLevel(logging.DEBUG)

        # 既存のハンドラーをクリア
        if logger.handlers:
            logger.handlers.clear()

        # ファイルハンドラー
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # フォーマッター
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        self.logger = logger
        return logger

    def _cleanup_old_logs(self):
        """古いログファイルを削除"""
        if not self.log_folder.exists():
            return

        log_files = sorted(
            self.log_folder.glob('stamp_maker_*.log'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # 最大ファイル数を超えた分を削除
        for log_file in log_files[self.max_log_files:]:
            try:
                log_file.unlink()
            except Exception:
                pass

    def get_logger(self):
        """ロガーを取得"""
        if self.logger is None:
            self.setup()
        return self.logger


# グローバルロガーインスタンス
_global_logger = None


def setup_logger(log_folder='./logs', max_log_files=30):
    """グローバルロガーをセットアップ"""
    global _global_logger
    _global_logger = StampMakerLogger(log_folder, max_log_files)
    return _global_logger.setup()


def get_logger():
    """グローバルロガーを取得"""
    global _global_logger
    if _global_logger is None:
        setup_logger()
    return _global_logger.get_logger()
