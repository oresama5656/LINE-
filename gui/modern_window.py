#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LINE Stamp Maker - Modern GUI Window (CustomTkinter)
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
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

# モジュールのインポート
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.config_manager import ConfigManager
from modules.logger import setup_logger
from modules.image_converter import ImageConverter
from modules.image_resizer import ImageResizer
from modules.zip_creator import ZipCreator


# CustomTkinterの設定
ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class Tk(ctk.CTk, TkinterDnD.DnDWrapper):
    """DnD対応のCustomTkinterルートウィンドウ"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


class ModernStampMakerGUI:
    """LINEスタンプ作成ツール - モダンGUI"""

    def __init__(self):
        # ルートウィンドウ作成
        if HAS_DND:
            self.root = Tk()
        else:
            self.root = ctk.CTk()

        # 設定とロガーの初期化
        self.config = ConfigManager('./config.json')
        self.logger = setup_logger(
            log_folder=self.config.get('logging.log_folder', './logs'),
            max_log_files=self.config.get('logging.max_log_files', 30)
        )
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
        self.root.title("LINE Stamp Maker Pro")
        self.root.geometry("700x800")
        self.root.resizable(True, True)

        # 変数
        self.folder_var = ctk.StringVar(value="ここにフォルダをドロップ")
        self.mode_var = ctk.StringVar(value=self.config.get('settings.resize_mode', 'fit'))
        self.output_var = ctk.StringVar(value=self.config.get('settings.output_base_path', 'C:\\LINE_OUTPUTS'))

        # 処理選択変数
        self.do_convert_var = ctk.BooleanVar(value=True)
        self.do_resize_var = ctk.BooleanVar(value=True)
        self.do_main_tab_var = ctk.BooleanVar(value=True)
        self.do_zip_var = ctk.BooleanVar(value=True)

        # main/tab選択変数
        self.main_file_path = None
        self.tab_file_path = None
        self.main_file_label_var = ctk.StringVar(value="未選択")
        self.tab_file_label_var = ctk.StringVar(value="未選択")

        # 進捗変数
        self.progress_var = ctk.DoubleVar(value=0)

        # GUI作成
        self.create_widgets()
        self.setup_layout()

        self.logger.info("Modern GUI initialized")

    def create_widgets(self):
        """ウィジェット作成"""
        # メインコンテナ
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ヘッダー
        self.header_label = ctk.CTkLabel(
            self.main_frame, 
            text="LINE Stamp Maker Pro", 
            font=("Roboto Medium", 24)
        )

        # 1. フォルダ選択セクション
        self.folder_frame = ctk.CTkFrame(self.main_frame)
        self.folder_label_title = ctk.CTkLabel(self.folder_frame, text="📂 対象フォルダ", font=("Roboto", 14, "bold"))
        
        self.folder_input_frame = ctk.CTkFrame(self.folder_frame, fg_color="transparent")
        self.folder_path_entry = ctk.CTkEntry(
            self.folder_input_frame, 
            textvariable=self.folder_var,
            placeholder_text="フォルダをドラッグ＆ドロップ",
            height=40,
            state="readonly"
        )
        
        self.browse_btn = ctk.CTkButton(
            self.folder_input_frame, 
            text="参照", 
            command=self.browse_folder,
            width=80,
            height=40
        )

        # 2. 設定セクション
        self.settings_frame = ctk.CTkFrame(self.main_frame)
        self.settings_label_title = ctk.CTkLabel(self.settings_frame, text="⚙️ 設定", font=("Roboto", 14, "bold"))

        # リサイズモード行
        self.mode_row_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.mode_label = ctk.CTkLabel(self.mode_row_frame, text="リサイズモード:")
        self.fit_radio = ctk.CTkRadioButton(self.mode_row_frame, text="縮小 (Fit)", variable=self.mode_var, value="fit")
        self.trim_radio = ctk.CTkRadioButton(self.mode_row_frame, text="トリミング (Trim)", variable=self.mode_var, value="trim")
        self.compact_radio = ctk.CTkRadioButton(self.mode_row_frame, text="余白なし (Compact)", variable=self.mode_var, value="compact")

        # 出力先行
        self.output_row_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.output_label = ctk.CTkLabel(self.output_row_frame, text="出力先:")
        self.output_entry = ctk.CTkEntry(self.output_row_frame, textvariable=self.output_var)
        self.output_browse_btn = ctk.CTkButton(self.output_row_frame, text="変更", command=self.browse_output_folder, width=60)
        self.save_config_btn = ctk.CTkButton(self.output_row_frame, text="設定保存", command=self.save_config, width=80, fg_color="gray")

        # 3. 処理オプションセクション
        self.process_frame = ctk.CTkFrame(self.main_frame)
        self.process_label_title = ctk.CTkLabel(self.process_frame, text="▶️ 処理フロー", font=("Roboto", 14, "bold"))

        # チェックボックス（2行に分ける）
        self.process_row1 = ctk.CTkFrame(self.process_frame, fg_color="transparent")
        self.convert_check = ctk.CTkCheckBox(self.process_row1, text="WebP → PNG変換", variable=self.do_convert_var)
        self.resize_check = ctk.CTkCheckBox(self.process_row1, text="リサイズ ＋ 連番リネーム", variable=self.do_resize_var)
        
        self.process_row2 = ctk.CTkFrame(self.process_frame, fg_color="transparent")
        self.main_tab_check = ctk.CTkCheckBox(self.process_row2, text="Main/Tab画像作成", variable=self.do_main_tab_var)
        self.zip_check = ctk.CTkCheckBox(self.process_row2, text="ZIP圧縮 (LINE提出用)", variable=self.do_zip_var)

        # Main/Tab画像選択エリア
        self.main_tab_area = ctk.CTkFrame(self.process_frame, fg_color=("gray90", "gray20"))
        
        # Main (Left)
        self.main_area = ctk.CTkFrame(self.main_tab_area, fg_color="transparent")
        self.main_img_label = ctk.CTkLabel(self.main_area, text="Main画像:")
        self.main_ctrl_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.main_file_btn = ctk.CTkButton(self.main_ctrl_frame, text="選択", command=self.select_main_image, width=60)
        self.main_file_name = ctk.CTkLabel(self.main_ctrl_frame, textvariable=self.main_file_label_var, text_color="gray")
        self.main_preview = ctk.CTkLabel(self.main_area, text="No Image", width=80, height=80, fg_color="gray10", corner_radius=5)

        # Tab (Right)
        self.tab_area = ctk.CTkFrame(self.main_tab_area, fg_color="transparent")
        self.tab_img_label = ctk.CTkLabel(self.tab_area, text="Tab画像:")
        self.tab_ctrl_frame = ctk.CTkFrame(self.tab_area, fg_color="transparent")
        self.tab_file_btn = ctk.CTkButton(self.tab_ctrl_frame, text="選択", command=self.select_tab_image, width=60)
        self.tab_file_name = ctk.CTkLabel(self.tab_ctrl_frame, textvariable=self.tab_file_label_var, text_color="gray")
        self.tab_preview = ctk.CTkLabel(self.tab_area, text="No Image", width=80, height=80, fg_color="gray10", corner_radius=5)

        # 4. アクションセクション
        self.action_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        
        self.start_btn = ctk.CTkButton(
            self.action_frame, 
            text="処理開始 (START)", 
            command=self.start_processing,
            font=("Roboto", 16, "bold"),
            height=50,
            fg_color="#2CC985",
            hover_color="#229965"
        )
        
        self.stop_btn = ctk.CTkButton(
            self.action_frame, 
            text="中止", 
            command=self.stop_processing,
            state="disabled",
            fg_color="#FF5555",
            hover_color="#CC4444",
            width=80
        )

        self.auto_prompter_btn = ctk.CTkButton(
            self.action_frame,
            text="AutoPrompter",
            command=self.launch_auto_prompter,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90")
        )

        # 5. ログ・進捗セクション
        self.log_frame = ctk.CTkFrame(self.main_frame)
        self.progress_bar = ctk.CTkProgressBar(self.log_frame, variable=self.progress_var)
        self.progress_bar.set(0)
        
        self.log_textbox = ctk.CTkTextbox(self.log_frame, height=150, font=("Consolas", 12))
        self.log_textbox.configure(state="disabled")

        # DnD設定
        if HAS_DND:
            self.folder_path_entry.drop_target_register(DND_FILES)
            self.folder_path_entry.dnd_bind('<<Drop>>', self.on_drop)
            self.folder_frame.drop_target_register(DND_FILES)
            self.folder_frame.dnd_bind('<<Drop>>', self.on_drop)

    def setup_layout(self):
        """レイアウト配置"""
        self.header_label.pack(pady=(0, 20))

        # 1. フォルダ選択
        self.folder_frame.pack(fill="x", pady=(0, 10))
        self.folder_label_title.pack(anchor="w", padx=10, pady=5)
        
        self.folder_input_frame.pack(fill="x", padx=10, pady=10)
        self.folder_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.browse_btn.pack(side="right", padx=(5, 0))

        # 2. 設定
        self.settings_frame.pack(fill="x", pady=(0, 10))
        self.settings_label_title.pack(anchor="w", padx=10, pady=5)
        
        # リサイズモード行
        self.mode_row_frame.pack(fill="x", padx=10, pady=5)
        self.mode_label.pack(side="left", padx=(0, 10))
        self.fit_radio.pack(side="left", padx=10)
        self.trim_radio.pack(side="left", padx=10)
        self.compact_radio.pack(side="left", padx=10)

        # 出力先行
        self.output_row_frame.pack(fill="x", padx=10, pady=5)
        self.output_label.pack(side="left", padx=(0, 10))
        self.save_config_btn.pack(side="right", padx=5)
        self.output_browse_btn.pack(side="right", padx=5)
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # 3. 処理オプション
        self.process_frame.pack(fill="x", pady=(0, 10))
        self.process_label_title.pack(anchor="w", padx=10, pady=5)
        
        self.process_row1.pack(fill="x", padx=10, pady=2)
        self.convert_check.pack(side="left", padx=10)
        self.resize_check.pack(side="left", padx=10)
        
        self.process_row2.pack(fill="x", padx=10, pady=2)
        self.main_tab_check.pack(side="left", padx=10)
        self.zip_check.pack(side="left", padx=10)

        # Main/Tabエリア
        self.main_tab_area.pack(fill="x", padx=10, pady=10)
        
        # Main (Left)
        self.main_area.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.main_img_label.pack(anchor="w")
        self.main_ctrl_frame.pack(fill="x", pady=5)
        self.main_file_btn.pack(side="left")
        self.main_file_name.pack(side="left", padx=5)
        self.main_preview.pack(pady=5)

        # Tab (Right)
        self.tab_area.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        self.tab_img_label.pack(anchor="w")
        self.tab_ctrl_frame.pack(fill="x", pady=5)
        self.tab_file_btn.pack(side="left")
        self.tab_file_name.pack(side="left", padx=5)
        self.tab_preview.pack(pady=5)

        # 4. アクション
        self.action_frame.pack(fill="x", pady=(0, 10))
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.stop_btn.pack(side="left", padx=(0, 10))
        self.auto_prompter_btn.pack(side="left")

        # 5. ログ
        self.log_frame.pack(fill="both", expand=True)
        self.progress_bar.pack(fill="x", padx=10, pady=(10, 5))
        self.log_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # DnD設定
        if HAS_DND:
            self.folder_path_entry.drop_target_register(DND_FILES)
            self.folder_path_entry.dnd_bind('<<Drop>>', self.on_drop)
            self.folder_frame.drop_target_register(DND_FILES)
            self.folder_frame.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        """ドラッグ&ドロップイベント処理"""
        dropped_path = event.data.strip('{}')
        if ' ' in dropped_path:
            dropped_path = dropped_path.split()[0].strip('{}')
        
        path = Path(dropped_path)
        if path.is_dir():
            self.selected_folder = path
            self.folder_var.set(str(self.selected_folder))
            self.add_log(f"📂 フォルダをセット: {self.selected_folder}")
        else:
            messagebox.showwarning("警告", "フォルダをドロップしてください")

    def browse_folder(self):
        folder = filedialog.askdirectory(title="スタンプフォルダを選択")
        if folder:
            self.selected_folder = Path(folder)
            self.folder_var.set(str(self.selected_folder))
            self.add_log(f"📂 フォルダを選択: {self.selected_folder}")

    def browse_output_folder(self):
        current = self.output_var.get()
        initial = current if Path(current).exists() else None
        folder = filedialog.askdirectory(title="出力先を選択", initialdir=initial)
        if folder:
            self.output_var.set(folder)
            self.add_log(f"出力先を変更: {folder}")

    def save_config(self):
        self.config.set('settings.resize_mode', self.mode_var.get())
        self.config.set('settings.output_base_path', self.output_var.get())
        self.config.save()
        self.add_log("✅ 設定を保存しました")
        # CTkのメッセージボックスがないので標準のものを使用
        messagebox.showinfo("保存完了", "設定を保存しました")

    def select_main_image(self):
        self._select_image_file('main')

    def select_tab_image(self):
        self._select_image_file('tab')

    def _select_image_file(self, image_type):
        if not self.selected_folder:
            messagebox.showerror("エラー", "先にスタンプフォルダを選択してください")
            return

        file_path = filedialog.askopenfilename(
            title=f"{image_type}画像を選択",
            initialdir=str(self.selected_folder),
            filetypes=[("画像", "*.png *.webp"), ("All", "*.*")]
        )

        if not file_path: return

        file_path = Path(file_path)
        try:
            file_path.relative_to(self.selected_folder)
        except ValueError:
            messagebox.showerror("エラー", "現在のフォルダ内の画像を選択してください")
            return

        if image_type == 'main':
            self.main_file_path = file_path
            self.main_file_label_var.set(file_path.name)
            self._update_preview('main', file_path)
        else:
            self.tab_file_path = file_path
            self.tab_file_label_var.set(file_path.name)
            self._update_preview('tab', file_path)
        
        self.add_log(f"🖼️ {image_type}画像を選択: {file_path.name}")

    def _update_preview(self, image_type, file_path):
        if not HAS_PIL: return
        try:
            img = Image.open(file_path)
            img.thumbnail((80, 80), Image.Resampling.LANCZOS)
            photo = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            
            if image_type == 'main':
                self.main_preview.configure(image=photo, text="")
            else:
                self.tab_preview.configure(image=photo, text="")
        except Exception as e:
            self.logger.error(f"Preview error: {e}")

    def add_log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"[{timestamp}] {message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
        self.root.update_idletasks()

    def start_processing(self):
        if not self.selected_folder:
            messagebox.showerror("エラー", "フォルダを選択してください")
            return
        
        if self.is_processing: return

        self.is_processing = True
        self.start_btn.configure(state="disabled", text="処理中...")
        self.stop_btn.configure(state="normal")
        self.progress_var.set(0)
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

        thread = threading.Thread(target=self.run_processing, daemon=True)
        thread.start()

    def stop_processing(self):
        self.is_processing = False
        self.add_log("⚠️ 処理を中止しました")
        self.on_processing_finished()

    def on_processing_finished(self):
        self.is_processing = False
        self.start_btn.configure(state="normal", text="処理開始 (START)")
        self.stop_btn.configure(state="disabled")
        self.progress_var.set(1.0)

    def run_processing(self):
        temp_folder = None
        try:
            import tempfile
            temp_folder = Path(tempfile.mkdtemp(prefix="line_stamp_"))
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_base = Path(self.output_var.get())
            output_base.mkdir(parents=True, exist_ok=True)
            final_zip_path = output_base / f"line_stamp_{timestamp}.zip"

            self.add_log(f"🚀 処理を開始します...")
            self.add_log(f"出力先: {output_base}")

            total_steps = sum([
                self.do_convert_var.get(),
                self.do_resize_var.get(),
                self.do_main_tab_var.get(),
                self.do_zip_var.get()
            ])
            current_step = 0

            converted_folder = temp_folder / "converted"

            # Step 1: Convert
            if self.do_convert_var.get() and self.is_processing:
                self.add_log("\n=== WebP → PNG変換 ===")
                if not self.image_converter.convert(self.selected_folder, converted_folder, self.add_log):
                    return
                current_step += 1
                self.progress_var.set(current_step / total_steps)

            # Step 2: Resize
            resized_folder = temp_folder / "resized"
            if self.do_resize_var.get() and self.is_processing:
                self.add_log("\n=== リサイズ処理 ===")
                input_for_resize = converted_folder if self.do_convert_var.get() and converted_folder.exists() else self.selected_folder
                if not self.image_resizer.resize(input_for_resize, resized_folder, self.mode_var.get(), self.add_log):
                    return
                current_step += 1
                self.progress_var.set(current_step / total_steps)

            # Step 3: Main/Tab
            if self.do_main_tab_var.get() and self.is_processing:
                self.add_log("\n=== Main/Tab画像作成 ===")
                if not self.main_file_path or not self.tab_file_path:
                    self.add_log("❌ Main/Tab画像が選択されていません")
                    return
                
                # Note: _create_main_tab_from_files is not implemented in this class, 
                # we should use the one from main_window.py or implement it here.
                # For now, let's implement a simple wrapper using Pillow directly or call a helper.
                # Actually, main_window.py had it as a method. Let's copy it.
                if not self._create_main_tab_from_files(resized_folder):
                    return
                
                current_step += 1
                self.progress_var.set(current_step / total_steps)

            # Step 4: ZIP
            if self.do_zip_var.get() and self.is_processing:
                self.add_log("\n=== ZIP作成 ===")
                if not self.zip_creator.create_zip(resized_folder, final_zip_path, self.add_log):
                    return
                current_step += 1
                self.progress_var.set(current_step / total_steps)

            self.add_log(f"\n✨ すべて完了しました！")
            self.add_log(f"📦 {final_zip_path.name}")

        except Exception as e:
            self.add_log(f"❌ エラー: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if temp_folder and temp_folder.exists():
                try:
                    shutil.rmtree(temp_folder)
                except: pass
            self.root.after(0, self.on_processing_finished)

    def _create_main_tab_from_files(self, output_folder):
        # Copied from main_window.py logic
        if not HAS_PIL: return False
        try:
            output_folder = Path(output_folder)
            output_folder.mkdir(parents=True, exist_ok=True)

            # Main
            self.add_log(f"🔄 main.png 作成中...")
            main_img = Image.open(self.main_file_path).convert('RGBA')
            main_img.thumbnail((240, 240), Image.Resampling.LANCZOS)
            main_canvas = Image.new('RGBA', (240, 240), (0, 0, 0, 0))
            x, y = (240 - main_img.width) // 2, (240 - main_img.height) // 2
            main_canvas.paste(main_img, (x, y), main_img)
            main_canvas.save(output_folder / 'main.png', 'PNG')

            # Tab
            self.add_log(f"🔄 tab.png 作成中...")
            tab_img = Image.open(self.tab_file_path).convert('RGBA')
            tab_img.thumbnail((96, 74), Image.Resampling.LANCZOS)
            tab_canvas = Image.new('RGBA', (96, 74), (0, 0, 0, 0))
            x, y = (96 - tab_img.width) // 2, (74 - tab_img.height) // 2
            tab_canvas.paste(tab_img, (x, y), tab_img)
            tab_canvas.save(output_folder / 'tab.png', 'PNG')

            return True
        except Exception as e:
            self.add_log(f"❌ Main/Tab作成エラー: {e}")
            return False

    def launch_auto_prompter(self):
        auto_prompter_path = Path(self.config.get('paths.auto_prompter'))
        if auto_prompter_path.exists():
            subprocess.Popen([str(auto_prompter_path)], shell=True)
            self.add_log("AutoPrompterを起動しました")
        else:
            messagebox.showerror("エラー", "AutoPrompterが見つかりません")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ModernStampMakerGUI()
    app.run()
