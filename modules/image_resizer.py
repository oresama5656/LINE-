#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Resizer Module
Calls Node.js resize scripts and creates main/tab images
"""

import subprocess
import shutil
from pathlib import Path
from typing import Callable, Optional, Tuple
from .logger import get_logger

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class ImageResizer:
    """画像リサイズクラス"""

    def __init__(self, line_stamp_maker_path: str, node_executable='node'):
        self.line_stamp_maker_path = Path(line_stamp_maker_path)
        self.node_executable = node_executable
        self.logger = get_logger()

    def resize(
        self,
        input_folder: Path,
        output_folder: Path,
        mode: str = 'fit',
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        画像リサイズ実行

        Args:
            input_folder: 入力フォルダ
            output_folder: 出力フォルダ
            mode: リサイズモード ('fit' or 'trim')
            progress_callback: 進捗コールバック

        Returns:
            成功した場合 True
        """
        if not input_folder.exists():
            self.logger.error(f"Input folder not found: {input_folder}")
            if progress_callback:
                progress_callback(f"❌ 入力フォルダが見つかりません: {input_folder}")
            return False

        # スクリプト選択
        if mode == 'trim':
            script_name = 'resize-only-trimming.js'
        else:
            script_name = 'resize-only.js'

        script_path = self.line_stamp_maker_path / script_name

        if not script_path.exists():
            self.logger.error(f"Script not found: {script_path}")
            if progress_callback:
                progress_callback(f"❌ スクリプトが見つかりません: {script_path}")
            return False

        try:
            # baseフォルダとoutputフォルダを準備
            base_folder = self.line_stamp_maker_path / 'base'
            temp_output = self.line_stamp_maker_path / 'output'

            # 既存のbase/outputフォルダをクリーンアップ
            if base_folder.exists():
                shutil.rmtree(base_folder)
            if temp_output.exists():
                shutil.rmtree(temp_output)

            base_folder.mkdir(parents=True, exist_ok=True)
            temp_output.mkdir(parents=True, exist_ok=True)

            # 入力画像をbaseフォルダにコピー（PNGのみ、WebPは除外）
            png_files = list(input_folder.glob('*.png'))

            if len(png_files) == 0:
                self.logger.warning("No PNG files found in input folder")
                if progress_callback:
                    progress_callback("⚠️ PNGファイルが見つかりません")
                return False

            # 同名のWebPファイルは除外（既にPNGに変換済みのため）
            unique_pngs = []
            for png in png_files:
                # .pngファイルのみを処理対象とする
                unique_pngs.append(png)

            if progress_callback:
                progress_callback(f"🔄 リサイズ中... ({len(unique_pngs)}ファイル, モード: {mode})")

            for img in unique_pngs:
                shutil.copy2(img, base_folder / img.name)

            self.logger.info(f"Copied {len(unique_pngs)} PNG files to base folder")

            # Node.jsスクリプト実行
            result = subprocess.run(
                [self.node_executable, script_path.name],
                cwd=str(self.line_stamp_maker_path),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if result.returncode != 0:
                self.logger.error(f"Resize failed: {result.stderr}")
                if progress_callback:
                    progress_callback(f"❌ リサイズ失敗: {result.stderr}")
                return False

            # output_folderに結果を移動
            output_folder.mkdir(parents=True, exist_ok=True)

            resized_files = list(temp_output.glob('*.png'))
            for file in resized_files:
                dest = output_folder / file.name
                shutil.copy2(file, dest)

            self.logger.info(f"Resized {len(resized_files)} files successfully")
            if progress_callback:
                progress_callback(f"✅ {len(resized_files)}ファイルをリサイズしました")

            return True

        except Exception as e:
            self.logger.error(f"Resize error: {e}")
            if progress_callback:
                progress_callback(f"❌ エラー: {e}")
            return False

    def create_main_tab(
        self,
        input_folder: Path,
        output_folder: Path,
        main_index: int,
        tab_index: int,
        mode: str = 'fit',
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        main.pngとtab.pngを作成

        Args:
            input_folder: 入力フォルダ（リサイズ済み画像）
            output_folder: 出力フォルダ
            main_index: main画像の番号（1-indexed）
            tab_index: tab画像の番号（1-indexed）
            mode: リサイズモード ('fit' or 'trim')
            progress_callback: 進捗コールバック

        Returns:
            成功した場合 True
        """
        if not input_folder.exists():
            self.logger.error(f"Input folder not found: {input_folder}")
            if progress_callback:
                progress_callback(f"❌ 入力フォルダが見つかりません: {input_folder}")
            return False

        # スクリプト選択
        if mode == 'trim':
            script_name = 'select-main-tab-trimming.js'
        else:
            script_name = 'select-main-tab-fit.js'

        script_path = self.line_stamp_maker_path / script_name

        if not script_path.exists():
            self.logger.error(f"Script not found: {script_path}")
            if progress_callback:
                progress_callback(f"❌ スクリプトが見つかりません: {script_path}")
            return False

        try:
            # outputフォルダを準備
            temp_output = self.line_stamp_maker_path / 'output'

            # 既存のmain.pngとtab.pngのみ削除（他のファイルは残す）
            if temp_output.exists():
                for old_file in ['main.png', 'tab.png']:
                    old_path = temp_output / old_file
                    if old_path.exists():
                        old_path.unlink()
            else:
                temp_output.mkdir(parents=True, exist_ok=True)

            # 入力画像をoutputフォルダにコピー（上書き）
            image_files = sorted(input_folder.glob('*.png'))

            if len(image_files) == 0:
                self.logger.warning("No PNG files found in input folder")
                if progress_callback:
                    progress_callback("⚠️ PNGファイルが見つかりません")
                return False

            if progress_callback:
                progress_callback(f"🔄 main/tab画像作成中... (main:{main_index}, tab:{tab_index})")

            for img in image_files:
                shutil.copy2(img, temp_output / img.name)

            # Node.jsスクリプトに選択番号を標準入力として渡す
            input_text = f"{main_index}\n{tab_index}\n"

            self.logger.debug(f"Running Node.js script: {script_path.name}")
            self.logger.debug(f"Input: {repr(input_text)}")

            result = subprocess.run(
                [self.node_executable, script_path.name],
                cwd=str(self.line_stamp_maker_path),
                input=input_text,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=30
            )

            self.logger.debug(f"Script return code: {result.returncode}")
            self.logger.debug(f"Script stdout: {result.stdout}")
            self.logger.debug(f"Script stderr: {result.stderr}")

            if result.returncode != 0:
                self.logger.error(f"Main/tab creation failed with return code {result.returncode}")
                self.logger.error(f"stderr: {result.stderr}")
                self.logger.error(f"stdout: {result.stdout}")
                if progress_callback:
                    progress_callback(f"❌ main/tab作成失敗: {result.stderr}")
                return False

            # main.pngとtab.pngを出力フォルダにコピー
            output_folder.mkdir(parents=True, exist_ok=True)

            main_file = temp_output / 'main.png'
            tab_file = temp_output / 'tab.png'

            copied_count = 0
            if main_file.exists():
                dest_main = output_folder / 'main.png'
                shutil.copy2(main_file, dest_main)
                self.logger.info(f"Copied main.png to {dest_main}")
                copied_count += 1
            else:
                self.logger.error(f"main.png not found in {temp_output}")

            if tab_file.exists():
                dest_tab = output_folder / 'tab.png'
                shutil.copy2(tab_file, dest_tab)
                self.logger.info(f"Copied tab.png to {dest_tab}")
                copied_count += 1
            else:
                self.logger.error(f"tab.png not found in {temp_output}")

            if copied_count == 0:
                self.logger.error("Failed to create main.png and tab.png")
                if progress_callback:
                    progress_callback("❌ main.pngとtab.pngが作成されませんでした")
                return False

            self.logger.info(f"Created and copied {copied_count} files successfully (main.png/tab.png)")
            if progress_callback:
                progress_callback(f"✅ main.pngとtab.pngを作成しました ({output_folder})")

            return True

        except Exception as e:
            self.logger.error(f"Main/tab creation error: {e}")
            if progress_callback:
                progress_callback(f"❌ エラー: {e}")
            return False

    def create_main_tab_python(
        self,
        input_folder: Path,
        output_folder: Path,
        main_index: int,
        tab_index: int,
        mode: str = 'fit',
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Pythonでmain.pngとtab.pngを作成（Pillow使用）

        Args:
            input_folder: 入力フォルダ（リサイズ済み画像）
            output_folder: 出力フォルダ
            main_index: main画像の番号（1-indexed）
            tab_index: tab画像の番号（1-indexed）
            mode: リサイズモード（使用しない、互換性のため）
            progress_callback: 進捗コールバック

        Returns:
            成功した場合 True
        """
        if not HAS_PIL:
            self.logger.error("Pillow is not installed")
            if progress_callback:
                progress_callback("❌ Pillowがインストールされていません")
            return False

        if not input_folder.exists():
            self.logger.error(f"Input folder not found: {input_folder}")
            if progress_callback:
                progress_callback(f"❌ 入力フォルダが見つかりません: {input_folder}")
            return False

        try:
            # PNG画像を取得（数字順にソート）
            image_files = sorted(
                input_folder.glob('*.png'),
                key=lambda f: int(f.stem) if f.stem.isdigit() else 999
            )

            # main.pngとtab.pngは除外
            image_files = [f for f in image_files if f.name.lower() not in ['main.png', 'tab.png']]

            if len(image_files) == 0:
                self.logger.error("No PNG files found in input folder")
                if progress_callback:
                    progress_callback("⚠️ PNGファイルが見つかりません")
                return False

            # インデックスの範囲チェック
            if main_index < 1 or main_index > len(image_files):
                self.logger.error(f"Main index out of range: {main_index} (1-{len(image_files)})")
                if progress_callback:
                    progress_callback(f"❌ main番号が範囲外です: {main_index} (1-{len(image_files)})")
                return False

            if tab_index < 1 or tab_index > len(image_files):
                self.logger.error(f"Tab index out of range: {tab_index} (1-{len(image_files)})")
                if progress_callback:
                    progress_callback(f"❌ tab番号が範囲外です: {tab_index} (1-{len(image_files)})")
                return False

            if progress_callback:
                progress_callback(f"🔄 main/tab画像作成中... (main:{main_index}, tab:{tab_index})")

            # 出力フォルダ作成
            output_folder.mkdir(parents=True, exist_ok=True)

            # main画像作成 (240×240px)
            main_source = image_files[main_index - 1]
            main_img = Image.open(main_source)

            # RGBAモードに変換（透過対応）
            if main_img.mode != 'RGBA':
                main_img = main_img.convert('RGBA')

            # アスペクト比を維持して縮小（containモード）
            main_img.thumbnail((240, 240), Image.Resampling.LANCZOS)

            # 240×240の透過背景キャンバスを作成
            main_canvas = Image.new('RGBA', (240, 240), (0, 0, 0, 0))

            # 中央配置
            x = (240 - main_img.width) // 2
            y = (240 - main_img.height) // 2
            main_canvas.paste(main_img, (x, y), main_img)

            # 保存
            main_path = output_folder / 'main.png'
            main_canvas.save(main_path, 'PNG')
            self.logger.info(f"Created main.png from {main_source.name}")

            # tab画像作成 (96×74px)
            tab_source = image_files[tab_index - 1]
            tab_img = Image.open(tab_source)

            # RGBAモードに変換
            if tab_img.mode != 'RGBA':
                tab_img = tab_img.convert('RGBA')

            # アスペクト比を維持して縮小
            tab_img.thumbnail((96, 74), Image.Resampling.LANCZOS)

            # 96×74の透過背景キャンバスを作成
            tab_canvas = Image.new('RGBA', (96, 74), (0, 0, 0, 0))

            # 中央配置
            x = (96 - tab_img.width) // 2
            y = (74 - tab_img.height) // 2
            tab_canvas.paste(tab_img, (x, y), tab_img)

            # 保存
            tab_path = output_folder / 'tab.png'
            tab_canvas.save(tab_path, 'PNG')
            self.logger.info(f"Created tab.png from {tab_source.name}")

            if progress_callback:
                progress_callback(f"✅ main.pngとtab.pngを作成しました")

            return True

        except Exception as e:
            self.logger.error(f"Main/tab creation error: {e}", exc_info=True)
            if progress_callback:
                progress_callback(f"❌ エラー: {e}")
            return False
