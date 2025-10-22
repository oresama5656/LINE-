#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZIP Creator Module for LINE Stamp
"""

import zipfile
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime
from .logger import get_logger


class ZipCreator:
    """LINEスタンプ用ZIP作成クラス"""

    def __init__(self):
        self.logger = get_logger()

    def create_zip(
        self,
        input_folder: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        LINEスタンプ用ZIPファイルを作成

        Args:
            input_folder: 入力フォルダ（リサイズ済み画像）
            output_path: 出力ZIPファイルパス
            progress_callback: 進捗コールバック

        Returns:
            成功した場合 True
        """
        if not input_folder.exists():
            self.logger.error(f"Input folder not found: {input_folder}")
            if progress_callback:
                progress_callback(f"❌ 入力フォルダが見つかりません: {input_folder}")
            return False

        try:
            # 必須ファイルのチェック
            main_file = input_folder / 'main.png'
            tab_file = input_folder / 'tab.png'

            if not main_file.exists():
                self.logger.error("main.png not found")
                if progress_callback:
                    progress_callback("❌ main.pngが見つかりません")
                return False

            if not tab_file.exists():
                self.logger.error("tab.png not found")
                if progress_callback:
                    progress_callback("❌ tab.pngが見つかりません")
                return False

            # スタンプ画像（01.png～40.png）を取得
            stamp_files = []
            for i in range(1, 41):
                stamp_file = input_folder / f'{i:02d}.png'
                if stamp_file.exists():
                    stamp_files.append(stamp_file)

            if len(stamp_files) == 0:
                self.logger.error("No stamp files (01.png~40.png) found")
                if progress_callback:
                    progress_callback("❌ スタンプ画像（01.png～）が見つかりません")
                return False

            # ZIPファイル作成
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if progress_callback:
                progress_callback(f"🔄 ZIP作成中... ({len(stamp_files)}個のスタンプ)")

            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # main.png
                zf.write(main_file, 'main.png')

                # tab.png
                zf.write(tab_file, 'tab.png')

                # スタンプ画像
                for stamp_file in stamp_files:
                    zf.write(stamp_file, stamp_file.name)

            self.logger.info(f"Created ZIP: {output_path} ({len(stamp_files)} stamps)")
            if progress_callback:
                progress_callback(f"✅ ZIP作成完了: {output_path.name} ({len(stamp_files)}個のスタンプ)")

            return True

        except Exception as e:
            self.logger.error(f"ZIP creation error: {e}")
            if progress_callback:
                progress_callback(f"❌ エラー: {e}")
            return False

    def create_auto_named_zip(
        self,
        input_folder: Path,
        output_folder: Path,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[Path]:
        """
        タイムスタンプ付きZIPファイルを自動生成

        Args:
            input_folder: 入力フォルダ
            output_folder: 出力フォルダ
            progress_callback: 進捗コールバック

        Returns:
            成功した場合、ZIPファイルのPath
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_name = f'line_stamp_{timestamp}.zip'
        zip_path = output_folder / zip_name

        if self.create_zip(input_folder, zip_path, progress_callback):
            return zip_path
        else:
            return None
