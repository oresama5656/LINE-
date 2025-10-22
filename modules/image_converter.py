#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Converter Module (WebP → PNG)
Calls Node.js convert-webp-to-png.js
"""

import subprocess
import shutil
from pathlib import Path
from typing import Callable, Optional
from .logger import get_logger


class ImageConverter:
    """WebP → PNG 変換クラス"""

    def __init__(self, line_stamp_maker_path: str, node_executable='node'):
        self.line_stamp_maker_path = Path(line_stamp_maker_path)
        self.node_executable = node_executable
        self.logger = get_logger()

    def check_needs_conversion(self, folder_path: Path) -> bool:
        """変換が必要かチェック（WebPファイルの有無）"""
        webp_files = list(folder_path.glob('*.webp'))
        return len(webp_files) > 0

    def convert(
        self,
        folder_path: Path,
        output_folder: Optional[Path] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        WebP → PNG 変換を実行

        Args:
            folder_path: 変換対象フォルダ（入力）
            output_folder: 出力フォルダ（Noneの場合は入力フォルダと同じ）
            progress_callback: 進捗コールバック関数

        Returns:
            成功した場合 True
        """
        if not folder_path.exists():
            self.logger.error(f"Folder not found: {folder_path}")
            if progress_callback:
                progress_callback(f"❌ フォルダが見つかりません: {folder_path}")
            return False

        # WebPファイルの有無をチェック
        if not self.check_needs_conversion(folder_path):
            self.logger.info("No WebP files found, skipping conversion")
            if progress_callback:
                progress_callback("ℹ️ WebPファイルがないためスキップします")
            return True

        # convert-webp-to-png.js のパス
        script_path = self.line_stamp_maker_path / 'convert-webp-to-png.js'

        if not script_path.exists():
            self.logger.error(f"Script not found: {script_path}")
            if progress_callback:
                progress_callback(f"❌ スクリプトが見つかりません: {script_path}")
            return False

        try:
            # 一時的に作業ディレクトリを変更してNode.jsスクリプトを実行
            # （スクリプトが __dirname ベースでファイルを処理するため）

            # まず、変換対象のWebPファイルをline_stamp_makerにコピー
            webp_files = list(folder_path.glob('*.webp'))
            temp_files = []

            if progress_callback:
                progress_callback(f"🔄 WebP → PNG 変換中... ({len(webp_files)}ファイル)")

            for webp_file in webp_files:
                dest = self.line_stamp_maker_path / webp_file.name
                shutil.copy2(webp_file, dest)
                temp_files.append(dest)

            self.logger.info(f"Copied {len(webp_files)} WebP files to line_stamp_maker")

            # Node.jsスクリプト実行
            result = subprocess.run(
                [self.node_executable, script_path.name],
                cwd=str(self.line_stamp_maker_path),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if result.returncode != 0:
                self.logger.error(f"Conversion failed: {result.stderr}")
                if progress_callback:
                    progress_callback(f"❌ 変換失敗: {result.stderr}")
                return False

            # 変換されたPNGファイルを出力フォルダに移動
            if output_folder is None:
                output_folder = folder_path

            output_folder.mkdir(parents=True, exist_ok=True)

            png_files = []
            for webp_file in webp_files:
                png_name = webp_file.stem + '.png'
                png_path = self.line_stamp_maker_path / png_name

                if png_path.exists():
                    dest = output_folder / png_name
                    shutil.move(str(png_path), str(dest))
                    png_files.append(dest)

            # 一時ファイル（WebP）を削除
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()

            self.logger.info(f"Converted {len(png_files)} files successfully")
            if progress_callback:
                progress_callback(f"✅ {len(png_files)}ファイルを変換しました")

            return True

        except Exception as e:
            self.logger.error(f"Conversion error: {e}")
            if progress_callback:
                progress_callback(f"❌ エラー: {e}")
            return False
