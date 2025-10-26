#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LINE Stamp Maker - Main GUI Window (Tkinter)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
from pathlib import Path
from datetime import datetime
import sys
import os
import shutil

# PIL for image thumbnail
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: Pillow not installed. Image preview will be disabled.")

# ドラッグ&ドロップサポート
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    print("Warning: tkinterdnd2 not installed. Drag & Drop will be disabled.")
    print("Install with: pip install tkinterdnd2")

# モジュールのインポート
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.config_manager import ConfigManager
from modules.logger import setup_logger
from modules.image_converter import ImageConverter
from modules.image_resizer import ImageResizer
from modules.zip_creator import ZipCreator


class StampMakerGUI:
    """LINEスタンプ作成ツール - メインGUI"""

    def __init__(self, root=None):
        if root is None:
            # ドラッグ&ドロップ対応のルートウィンドウ作成
            if HAS_DND:
                self.root = TkinterDnD.Tk()
            else:
                self.root = tk.Tk()
            self.owns_root = True
        else:
            self.root = root
            self.owns_root = False

        # 設定とロガーの初期化
        self.config = ConfigManager('./config.json')
        self.logger = setup_logger(
            log_folder=self.config.get('logging.log_folder', './logs'),
            max_log_files=self.config.get('logging.max_log_files', 30)
        )
        # DEBUGレベルに変更
        self.logger.setLevel(10)  # DEBUG

        # モジュール初期化
        self.image_converter = ImageConverter(
            self.config.get('paths.line_stamp_maker'),
            self.config.get('paths.node_executable', 'node')
        )
        self.image_resizer = ImageResizer(
            self.config.get('paths.line_stamp_maker'),
            self.config.get('paths.node_executable', 'node')
        )
        self.zip_creator = ZipCreator()

        # 状態管理
        self.is_processing = False
        self.selected_folder = None

        # ウィンドウ設定
        self.root.title("LINEスタンプ自動生成ツール - ver 1.0")
        self.root.geometry("600x600")
        self.root.resizable(True, True)

        # 変数
        self.folder_var = tk.StringVar(value="ここにスタンプフォルダをドラッグ＆ドロップ")
        self.mode_var = tk.StringVar(value="fit")
        self.output_var = tk.StringVar(value=self.config.get('settings.output_base_path', 'C:\\LINE_OUTPUTS'))

        # 処理選択変数
        self.do_convert_var = tk.BooleanVar(value=True)
        self.do_resize_var = tk.BooleanVar(value=True)
        self.do_main_tab_var = tk.BooleanVar(value=True)
        self.do_zip_var = tk.BooleanVar(value=True)

        # main/tab選択変数（ファイルパス保持）
        self.main_file_path = None
        self.tab_file_path = None
        self.main_file_label_var = tk.StringVar(value="未選択")
        self.tab_file_label_var = tk.StringVar(value="未選択")

        # サムネイル画像保持
        self.main_thumbnail = None
        self.tab_thumbnail = None

        # 進捗変数
        self.progress_var = tk.DoubleVar(value=0)

        # GUI作成
        self.create_widgets()
        self.setup_layout()

        self.logger.info("GUI initialized")

    def create_widgets(self):
        """ウィジェット作成"""
        # 上部フレーム（後でsetup_layoutで使用）
        self.top_frame = ttk.Frame(self.root)

        # フォルダ選択フレーム
        self.folder_frame = ttk.LabelFrame(self.top_frame, text="📂 ドロップまたは選択", padding="5")

        self.folder_label = ttk.Label(
            self.folder_frame,
            textvariable=self.folder_var,
            relief="solid",
            borderwidth=2,
            padding=10,
            background="#f0f0f0",
            anchor="center"
        )

        self.browse_btn = ttk.Button(self.folder_frame, text="フォルダを選択", command=self.browse_folder)

        # 設定フレーム
        self.settings_frame = ttk.LabelFrame(self.top_frame, text="⚙️ 設定", padding="5")

        ttk.Label(self.settings_frame, text="リサイズモード:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.fit_radio = ttk.Radiobutton(self.settings_frame, text="縮小", variable=self.mode_var, value="fit")
        self.fit_radio.grid(row=0, column=1, sticky="w")
        self.trim_radio = ttk.Radiobutton(self.settings_frame, text="トリミング", variable=self.mode_var, value="trim")
        self.trim_radio.grid(row=0, column=2, sticky="w", padx=(10, 0))

        ttk.Label(self.settings_frame, text="出力先:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(10, 0))
        self.output_entry = ttk.Entry(self.settings_frame, textvariable=self.output_var, width=30)
        self.output_entry.grid(row=1, column=1, sticky="ew", pady=(10, 0))

        self.output_browse_btn = ttk.Button(self.settings_frame, text="参照...", command=self.browse_output_folder)
        self.output_browse_btn.grid(row=1, column=2, sticky="w", padx=(5, 0), pady=(10, 0))

        self.save_config_btn = ttk.Button(self.settings_frame, text="設定を保存", command=self.save_config)
        self.save_config_btn.grid(row=2, column=0, columnspan=3, pady=(10, 0))

        # 処理選択フレーム
        self.process_frame = ttk.LabelFrame(self.root, text="▶️ 処理内容選択", padding="5")

        # チェックボックスとラベルを分離（テキスト部分のクリックを無効化）
        convert_frame = ttk.Frame(self.process_frame)
        convert_frame.pack(anchor="w", pady=2)
        self.convert_check = ttk.Checkbutton(
            convert_frame,
            variable=self.do_convert_var
        )
        self.convert_check.pack(side="left")
        ttk.Label(convert_frame, text="webp→png変換（pngなら自動スキップ）").pack(side="left", padx=(5, 0))

        resize_frame = ttk.Frame(self.process_frame)
        resize_frame.pack(anchor="w", pady=2)
        self.resize_check = ttk.Checkbutton(
            resize_frame,
            variable=self.do_resize_var
        )
        self.resize_check.pack(side="left")
        ttk.Label(resize_frame, text="リサイズ＋リネーム").pack(side="left", padx=(5, 0))

        # main/tab選択フレーム
        self.main_tab_frame = ttk.LabelFrame(self.process_frame, text="", padding="5")
        self.main_tab_frame.pack(anchor="w", pady=5, fill="x")

        main_tab_check_frame = ttk.Frame(self.main_tab_frame)
        main_tab_check_frame.grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 5))
        self.main_tab_check = ttk.Checkbutton(
            main_tab_check_frame,
            variable=self.do_main_tab_var
        )
        self.main_tab_check.pack(side="left")
        ttk.Label(main_tab_check_frame, text="tab/main画像を作成").pack(side="left", padx=(5, 0))

        # main画像選択（左側）
        ttk.Label(self.main_tab_frame, text="main画像:").grid(row=1, column=0, sticky="w", padx=(0, 5))
        self.main_file_btn = ttk.Button(
            self.main_tab_frame,
            text="画像を選択...",
            command=self.select_main_image,
            width=12
        )
        self.main_file_btn.grid(row=1, column=1, sticky="w", padx=(0, 5))
        self.main_file_label = ttk.Label(
            self.main_tab_frame,
            textvariable=self.main_file_label_var,
            foreground="gray",
            width=15
        )
        self.main_file_label.grid(row=1, column=2, sticky="w", padx=(0, 10))

        # tab画像選択（右側）
        ttk.Label(self.main_tab_frame, text="tab画像:").grid(row=1, column=3, sticky="w", padx=(0, 5))
        self.tab_file_btn = ttk.Button(
            self.main_tab_frame,
            text="画像を選択...",
            command=self.select_tab_image,
            width=12
        )
        self.tab_file_btn.grid(row=1, column=4, sticky="w", padx=(0, 5))
        self.tab_file_label = ttk.Label(
            self.main_tab_frame,
            textvariable=self.tab_file_label_var,
            foreground="gray",
            width=15
        )
        self.tab_file_label.grid(row=1, column=5, sticky="w")

        # プレビュー（main左、tab右）
        self.main_preview_label = ttk.Label(self.main_tab_frame, text="")
        self.main_preview_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(2, 0))

        self.tab_preview_label = ttk.Label(self.main_tab_frame, text="")
        self.tab_preview_label.grid(row=2, column=3, columnspan=3, sticky="w", pady=(2, 0))

        zip_frame = ttk.Frame(self.process_frame)
        zip_frame.pack(anchor="w", pady=2)
        self.zip_check = ttk.Checkbutton(
            zip_frame,
            variable=self.do_zip_var
        )
        self.zip_check.pack(side="left")
        ttk.Label(zip_frame, text="ZIP作成（LINEスタンプ用）").pack(side="left", padx=(5, 0))

        # 実行ボタンフレーム
        self.button_frame = ttk.Frame(self.root, padding="5")

        self.start_btn = ttk.Button(self.button_frame, text="すべて実行", command=self.start_processing, width=20)
        self.start_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ttk.Button(self.button_frame, text="中止", command=self.stop_processing, state="disabled", width=15)
        self.stop_btn.pack(side="left", padx=(0, 10))

        self.auto_prompter_btn = ttk.Button(self.button_frame, text="AutoPrompterを起動", command=self.launch_auto_prompter, width=20)
        self.auto_prompter_btn.pack(side="left")

        # 進捗フレーム
        self.progress_frame = ttk.LabelFrame(self.root, text="進捗状況", padding="5")

        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=(0, 10))

        # ログフレーム
        self.log_frame = ttk.LabelFrame(self.root, text="ログ", padding="5")

        self.log_text = tk.Text(self.log_frame, height=6, width=70, font=("Consolas", 9), wrap="word")
        self.log_scrollbar = ttk.Scrollbar(self.log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scrollbar.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        self.log_scrollbar.pack(side="right", fill="y")

        # ログテキストのタグ設定
        self.log_text.tag_configure("info", foreground="black")
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("warning", foreground="orange")

    def setup_layout(self):
        """レイアウト設定"""
        # 上部：フォルダ選択と設定を横並び
        self.top_frame.pack(fill="x", padx=5, pady=5)

        self.folder_frame.pack(side="left", fill="both", expand=True, padx=(0, 3))
        self.folder_label.pack(fill="x", pady=(0, 5))
        self.browse_btn.pack()

        self.settings_frame.pack(side="left", fill="both", expand=True, padx=(3, 0))
        self.settings_frame.columnconfigure(1, weight=1)

        self.process_frame.pack(fill="x", padx=5, pady=5)

        self.button_frame.pack(fill="x", padx=5, pady=5)

        self.progress_frame.pack(fill="x", padx=5, pady=5)

        self.log_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # ドラッグ＆ドロップ設定
        if HAS_DND:
            self.folder_label.drop_target_register(DND_FILES)
            self.folder_label.dnd_bind('<<Drop>>', self.on_drop)

        # クリックでもフォルダ選択可能
        self.folder_label.bind("<Button-1>", lambda e: self.browse_folder())

    def on_drop(self, event):
        """ドラッグ&ドロップイベント処理"""
        # ドロップされたパスを取得（波括弧で囲まれている場合があるので除去）
        dropped_path = event.data.strip('{}')

        # 複数ファイルがドロップされた場合は最初のパスを使用
        if ' ' in dropped_path:
            dropped_path = dropped_path.split()[0].strip('{}')

        path = Path(dropped_path)

        # ディレクトリかチェック
        if path.is_dir():
            self.selected_folder = path
            self.folder_var.set(str(self.selected_folder))
            self.add_log(f"フォルダをドロップ: {self.selected_folder}", "info")
        else:
            messagebox.showwarning("警告", "フォルダをドロップしてください（ファイルは不可）")

        return event.action

    def browse_folder(self):
        """フォルダ選択ダイアログ"""
        folder = filedialog.askdirectory(title="スタンプフォルダを選択")
        if folder:
            self.selected_folder = Path(folder)
            self.folder_var.set(str(self.selected_folder))
            self.add_log(f"フォルダを選択: {self.selected_folder}", "info")

    def browse_output_folder(self):
        """出力先フォルダ選択ダイアログ"""
        current_output = self.output_var.get()
        initial_dir = current_output if Path(current_output).exists() else None
        folder = filedialog.askdirectory(
            title="出力先フォルダを選択",
            initialdir=initial_dir
        )
        if folder:
            self.output_var.set(folder)
            self.add_log(f"出力先を設定: {folder}", "info")

    def select_main_image(self):
        """main画像選択"""
        self._select_image_file('main')

    def select_tab_image(self):
        """tab画像選択"""
        self._select_image_file('tab')

    def _select_image_file(self, image_type):
        """
        画像ファイル選択（共通処理）

        Args:
            image_type: 'main' または 'tab'
        """
        if not self.selected_folder:
            messagebox.showerror("選択エラー", "先にスタンプフォルダを選択してください")
            return

        # ファイル選択ダイアログ
        file_path = filedialog.askopenfilename(
            title=f"{image_type}画像を選択",
            initialdir=str(self.selected_folder),
            filetypes=[
                ("画像ファイル", "*.png *.webp"),
                ("PNG", "*.png"),
                ("WebP", "*.webp"),
                ("すべて", "*.*")
            ]
        )

        if not file_path:
            return  # キャンセル

        file_path = Path(file_path)

        # フォルダ検証: 選択されたファイルが現在のフォルダ内にあるか
        try:
            file_path.relative_to(self.selected_folder)
        except ValueError:
            messagebox.showerror(
                "選択エラー",
                "現在のフォルダ内の画像を選択してください。"
            )
            return

        # 正常な選択
        if image_type == 'main':
            self.main_file_path = file_path
            self.main_file_label_var.set(file_path.name)
            self._update_preview('main', file_path)
        else:  # tab
            self.tab_file_path = file_path
            self.tab_file_label_var.set(file_path.name)
            self._update_preview('tab', file_path)

        self.add_log(f"{image_type}画像を選択: {file_path.name}", "info")

    def _update_preview(self, image_type, file_path):
        """
        プレビュー画像更新

        Args:
            image_type: 'main' または 'tab'
            file_path: 画像ファイルパス
        """
        if not HAS_PIL:
            return

        try:
            # 画像読み込み
            img = Image.open(file_path)

            # サムネイルサイズ（軽量化のため）
            max_size = (80, 80)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # PhotoImage作成
            photo = ImageTk.PhotoImage(img)

            # プレビュー表示
            if image_type == 'main':
                self.main_thumbnail = photo  # 参照保持
                self.main_preview_label.config(image=photo)
            else:  # tab
                self.tab_thumbnail = photo  # 参照保持
                self.tab_preview_label.config(image=photo)

        except Exception as e:
            self.logger.error(f"Preview error for {image_type}: {e}")

    def _create_main_tab_from_files(self, output_folder):
        """
        選択されたファイルからmain.pngとtab.pngを作成

        Args:
            output_folder: 出力フォルダ

        Returns:
            成功した場合 True
        """
        if not HAS_PIL:
            self.add_log("❌ Pillowがインストールされていません", "error")
            return False

        try:
            output_folder = Path(output_folder)
            output_folder.mkdir(parents=True, exist_ok=True)

            # main画像作成 (240×240px)
            self.add_log(f"🔄 main.png を作成中... ({self.main_file_path.name})", "info")
            main_img = Image.open(self.main_file_path)

            # RGBAモードに変換（透過対応）
            if main_img.mode != 'RGBA':
                main_img = main_img.convert('RGBA')

            # アスペクト比を維持して縮小
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
            self.logger.info(f"Created main.png from {self.main_file_path.name}")

            # tab画像作成 (96×74px)
            self.add_log(f"🔄 tab.png を作成中... ({self.tab_file_path.name})", "info")
            tab_img = Image.open(self.tab_file_path)

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
            self.logger.info(f"Created tab.png from {self.tab_file_path.name}")

            self.add_log("✅ main.pngとtab.pngを作成しました", "success")
            return True

        except Exception as e:
            self.logger.error(f"Main/tab creation error: {e}", exc_info=True)
            self.add_log(f"❌ エラー: {e}", "error")
            return False

    def save_config(self):
        """設定を保存"""
        self.config.set('settings.resize_mode', self.mode_var.get())
        self.config.set('settings.output_base_path', self.output_var.get())
        self.config.save()
        self.add_log("設定を保存しました", "success")
        messagebox.showinfo("保存完了", "設定を保存しました")

    def start_processing(self):
        """処理開始"""
        if not self.selected_folder:
            messagebox.showerror("エラー", "フォルダを選択してください")
            return

        if self.is_processing:
            messagebox.showwarning("警告", "処理中です")
            return

        # 少なくとも1つの処理が選択されているか確認
        if not any([
            self.do_convert_var.get(),
            self.do_resize_var.get(),
            self.do_main_tab_var.get(),
            self.do_zip_var.get()
        ]):
            messagebox.showwarning("警告", "少なくとも1つの処理を選択してください")
            return

        self.is_processing = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.progress_var.set(0)
        self.log_text.delete(1.0, tk.END)

        # 別スレッドで処理実行
        thread = threading.Thread(target=self.run_processing, daemon=True)
        thread.start()

    def stop_processing(self):
        """処理中止"""
        self.is_processing = False
        self.add_log("処理を中止しました", "warning")
        self.on_processing_finished()

    def run_processing(self):
        """処理実行（別スレッド）"""
        temp_folder = None
        try:
            # 一時フォルダ作成（処理後に削除）
            import tempfile
            temp_folder = Path(tempfile.mkdtemp(prefix="line_stamp_"))

            # 出力先フォルダ
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_base = Path(self.output_var.get())
            output_base.mkdir(parents=True, exist_ok=True)

            # ZIPファイルの最終出力パス
            final_zip_path = output_base / f"line_stamp_{timestamp}.zip"

            self.add_log(f"出力先: {output_base}", "info")
            self.logger.info(f"Processing started: {self.selected_folder} -> {output_base}")

            total_steps = sum([
                self.do_convert_var.get(),
                self.do_resize_var.get(),
                self.do_main_tab_var.get(),
                self.do_zip_var.get()
            ])
            current_step = 0

            # 変換後のPNG保存先（一時フォルダ）
            converted_folder = temp_folder / "converted"

            # Step 1: webp→png変換
            if self.do_convert_var.get() and self.is_processing:
                self.add_log("\n=== webp→png変換 ===", "info")
                success = self.image_converter.convert(
                    self.selected_folder,
                    converted_folder,
                    self.add_log
                )
                if not success:
                    self.add_log("変換に失敗しました", "error")
                    return

                current_step += 1
                self.progress_var.set((current_step / total_steps) * 100)

            # Step 2: リサイズ＋リネーム
            resized_folder = temp_folder / "resized"
            if self.do_resize_var.get() and self.is_processing:
                self.add_log("\n=== リサイズ＋リネーム ===", "info")

                # WebP変換を実行した場合は変換後のフォルダを使用、そうでなければ元のフォルダ
                input_for_resize = converted_folder if self.do_convert_var.get() and converted_folder.exists() else self.selected_folder

                success = self.image_resizer.resize(
                    input_for_resize,
                    resized_folder,
                    self.mode_var.get(),
                    self.add_log
                )
                if not success:
                    self.add_log("リサイズに失敗しました", "error")
                    return

                current_step += 1
                self.progress_var.set((current_step / total_steps) * 100)

            # Step 3: main/tab作成
            if self.do_main_tab_var.get() and self.is_processing:
                self.add_log("\n=== main/tab画像作成 ===", "info")

                # ファイル選択チェック
                if not self.main_file_path or not self.tab_file_path:
                    self.add_log("❌ main画像とtab画像を選択してください", "error")
                    return

                # 選択されたファイルをリサイズして作成
                success = self._create_main_tab_from_files(resized_folder)
                if not success:
                    self.add_log("main/tab作成に失敗しました", "error")
                    return

                current_step += 1
                self.progress_var.set((current_step / total_steps) * 100)

            # Step 4: ZIP作成
            if self.do_zip_var.get() and self.is_processing:
                self.add_log("\n=== ZIP作成 ===", "info")

                # ZIPファイルを出力先フォルダ直下に作成
                success = self.zip_creator.create_zip(
                    resized_folder,
                    final_zip_path,
                    self.add_log
                )

                if not success:
                    self.add_log("ZIP作成に失敗しました", "error")
                    return

                current_step += 1
                self.progress_var.set((current_step / total_steps) * 100)

            self.add_log(f"\n🎉 すべての処理が完了しました！", "success")
            self.add_log(f"📦 出力ファイル: {final_zip_path.name}", "success")
            self.logger.info("Processing completed successfully")

        except Exception as e:
            self.add_log(f"エラーが発生しました: {e}", "error")
            self.logger.error(f"Processing error: {e}", exc_info=True)

        finally:
            # 一時フォルダのクリーンアップ
            if temp_folder and temp_folder.exists():
                try:
                    shutil.rmtree(temp_folder)
                    self.logger.info(f"Cleaned up temporary folder: {temp_folder}")
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup temp folder: {e}")

            self.root.after(0, self.on_processing_finished)

    def on_processing_finished(self):
        """処理完了時のUI更新"""
        self.is_processing = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.progress_var.set(100)

    def launch_auto_prompter(self):
        """AutoPrompterを起動"""
        auto_prompter_path = Path(self.config.get('paths.auto_prompter'))

        if not auto_prompter_path.exists():
            messagebox.showerror("エラー", f"AutoPrompterが見つかりません:\n{auto_prompter_path}")
            return

        try:
            subprocess.Popen([str(auto_prompter_path)], shell=True)
            self.add_log("AutoPrompterを起動しました", "info")
        except Exception as e:
            self.add_log(f"AutoPrompter起動エラー: {e}", "error")
            messagebox.showerror("エラー", f"起動に失敗しました:\n{e}")

    def add_log(self, message: str, tag: str = "info"):
        """ログ追加"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"

        self.log_text.insert(tk.END, log_line, tag)
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def run(self):
        """GUIメインループ"""
        if self.owns_root:
            self.root.mainloop()


if __name__ == "__main__":
    gui = StampMakerGUI()
    gui.run()
