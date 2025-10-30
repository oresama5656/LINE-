#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatGPT GUI Main Window - Clean Version
Simple tkinter-based GUI without encoding issues
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path
from typing import Optional, Callable


class ChatGPTGUIWindow:
    """Main GUI Window"""
    
    def __init__(self, root: Optional[tk.Tk] = None):
        if root is None:
            self.root = tk.Tk()
            self.owns_root = True
        else:
            self.root = root
            self.owns_root = False
        
        # Window setup
        self.root.title("ChatGPT GUI Auto - Control Panel")
        self.root.geometry("480x600")  # Compacted: 800x900 -> 480x600 (40% width cut, height reduced)
        self.root.resizable(True, True)
        
        # State management
        self.is_running = False
        
        # Variables
        self.csv_var = tk.StringVar()
        self.wait_var = tk.StringVar(value="120") # Increased from 60 to 120
        self.dry_run_var = tk.BooleanVar(value=False)
        self.interactive_var = tk.BooleanVar(value=True)
        self.max_items_var = tk.StringVar(value="50")
        self.retry_var = tk.StringVar(value="0")
        self.prefix_var = tk.StringVar(value="")
        self.suffix_var = tk.StringVar(value="")
        self.speed_var = tk.StringVar(value="高速")  # 操作速度設定
        self.mode_var = tk.StringVar(value="gui")  # CSV/GUIモード切り替え（デフォルト: GUI Mode）
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Ready")
        
        # Callbacks
        self.on_start_callback: Optional[Callable] = None
        self.on_stop_callback: Optional[Callable] = None

        # Create GUI
        self.create_widgets()
        self.setup_layout()
        
    def create_widgets(self):
        """Create GUI widgets"""
        # CSV File frame - 1行目
        self.csv_frame = ttk.Frame(self.root, padding="5")
        ttk.Label(self.csv_frame, text="CSV:").pack(side="left", padx=(0,5))
        self.csv_entry = ttk.Entry(self.csv_frame, textvariable=self.csv_var, width=42)
        self.csv_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        self.browse_btn = ttk.Button(self.csv_frame, text="参照", command=self.browse_csv, width=4)
        self.browse_btn.pack(side="left")

        # Settings frame - 2行に分ける
        self.settings_frame = ttk.LabelFrame(self.root, text="Settings", padding="5")

        # Settings 1行目
        self.settings_row1 = ttk.Frame(self.settings_frame)
        ttk.Label(self.settings_row1, text="Wait:").pack(side="left", padx=(0,3))
        self.wait_entry = ttk.Entry(self.settings_row1, textvariable=self.wait_var, width=5)
        self.wait_entry.pack(side="left", padx=(0,12))

        self.dry_run_check = ttk.Checkbutton(self.settings_row1, text="Dry Run", variable=self.dry_run_var)
        self.dry_run_check.pack(side="left", padx=(0,12))

        self.interactive_check = ttk.Checkbutton(self.settings_row1, text="Interactive", variable=self.interactive_var)
        self.interactive_check.pack(side="left", padx=(0,12))

        ttk.Label(self.settings_row1, text="Max Items:").pack(side="left", padx=(0,3))
        self.max_items_entry = ttk.Entry(self.settings_row1, textvariable=self.max_items_var, width=5)
        self.max_items_entry.pack(side="left")

        # Settings 2行目
        self.settings_row2 = ttk.Frame(self.settings_frame)
        ttk.Label(self.settings_row2, text="Retry:").pack(side="left", padx=(0,3))
        self.retry_entry = ttk.Entry(self.settings_row2, textvariable=self.retry_var, width=5)
        self.retry_entry.pack(side="left", padx=(0,12))

        ttk.Label(self.settings_row2, text="Speed:").pack(side="left", padx=(0,3))
        self.speed_combo = ttk.Combobox(self.settings_row2, textvariable=self.speed_var, width=6, state="readonly")
        self.speed_combo['values'] = ('高速', '中速', '低速')
        self.speed_combo.pack(side="left", padx=(0,12))
        self.speed_combo.bind('<<ComboboxSelected>>', self.update_speed_description)

        ttk.Label(self.settings_row2, text="Mode:").pack(side="left", padx=(0,5))
        self.gui_mode_radio = ttk.Radiobutton(self.settings_row2, text="GUI", variable=self.mode_var, value="gui", command=self.on_mode_changed)
        self.gui_mode_radio.pack(side="left", padx=(0,5))
        self.csv_mode_radio = ttk.Radiobutton(self.settings_row2, text="CSV", variable=self.mode_var, value="csv", command=self.on_mode_changed)
        self.csv_mode_radio.pack(side="left")

        # Prefix と Suffix を1行にまとめる
        self.prefix_suffix_frame = ttk.Frame(self.root, padding="5")

        # Prefix (左半分)
        self.prefix_frame = ttk.LabelFrame(self.prefix_suffix_frame, text="Prefix", padding="3")
        self.prefix_text = tk.Text(self.prefix_frame, height=2, width=24, font=("Consolas", 9), wrap="word")
        self.prefix_scrollbar = ttk.Scrollbar(self.prefix_frame, orient="vertical", command=self.prefix_text.yview)
        self.prefix_text.configure(yscrollcommand=self.prefix_scrollbar.set)
        self.prefix_text.pack(side="left", fill="both", expand=True)
        self.prefix_scrollbar.pack(side="right", fill="y")
        self.prefix_frame.pack(side="left", fill="both", expand=True, padx=(0,5))

        # Suffix (右半分)
        self.suffix_frame = ttk.LabelFrame(self.prefix_suffix_frame, text="Suffix", padding="3")
        self.suffix_text = tk.Text(self.suffix_frame, height=2, width=24, font=("Consolas", 9), wrap="word")
        self.suffix_scrollbar = ttk.Scrollbar(self.suffix_frame, orient="vertical", command=self.suffix_text.yview)
        self.suffix_text.configure(yscrollcommand=self.suffix_scrollbar.set)
        self.suffix_text.pack(side="left", fill="both", expand=True)
        self.suffix_scrollbar.pack(side="right", fill="y")
        self.suffix_frame.pack(side="left", fill="both", expand=True)

        # Control frame - ボタンとプログレスバー
        self.control_frame = ttk.Frame(self.root, padding="5")

        # ボタン（1行目）
        self.button_row = ttk.Frame(self.control_frame)
        self.start_btn = ttk.Button(self.button_row, text="Start", command=self.on_start, width=10)
        self.stop_btn = ttk.Button(self.button_row, text="Stop", command=self.on_stop, state="disabled", width=10)
        self.clear_btn = ttk.Button(self.button_row, text="Clear Log", command=self.clear_log, width=10)

        # プログレスバー（2行目）
        self.progress_row = ttk.Frame(self.control_frame)
        self.progress_bar = ttk.Progressbar(self.progress_row, variable=self.progress_var, maximum=100, length=300)

        # ステータス（3行目）
        self.status_row = ttk.Frame(self.control_frame)
        self.status_label = ttk.Label(self.status_row, textvariable=self.status_var, width=60)

        # Log frame - ログ行数を15行に調整
        self.log_frame = ttk.LabelFrame(self.root, text="Log", padding="5")
        self.log_text = tk.Text(self.log_frame, height=15, width=55, font=("Consolas", 8))
        self.log_scrollbar = ttk.Scrollbar(self.log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scrollbar.set)
        
        # Log tags for coloring
        self.log_text.tag_configure("info", foreground="black")
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("warning", foreground="orange")
        self.log_text.tag_configure("debug", foreground="gray")
        
    def setup_layout(self):
        """Setup layout"""
        # CSV frame - 1行目
        self.csv_frame.pack(fill="x", padx=3, pady=3)

        # Settings frame - 2行目・3行目
        self.settings_frame.pack(fill="x", padx=3, pady=3)
        self.settings_row1.pack(fill="x", pady=(0,3))
        self.settings_row2.pack(fill="x")

        # Prefix & Suffix - 4行目
        self.prefix_suffix_frame.pack(fill="x", padx=3, pady=3)

        # Control frame - 5行目（ボタン）、6行目（プログレスバー）、7行目（ステータス）
        self.control_frame.pack(fill="x", padx=3, pady=3)
        self.button_row.pack(fill="x", pady=(0,3))
        self.start_btn.pack(side="left", padx=(0,5))
        self.stop_btn.pack(side="left", padx=(0,5))
        self.clear_btn.pack(side="left")
        self.progress_row.pack(fill="x", pady=(0,2))
        self.progress_bar.pack(fill="x", expand=True)
        self.status_row.pack(fill="x")
        self.status_label.pack(fill="x", expand=True)

        # Log - 8行目
        self.log_frame.pack(fill="both", expand=True, padx=3, pady=3)
        self.log_text.pack(side="left", fill="both", expand=True)
        self.log_scrollbar.pack(side="right", fill="y")
    
    def browse_csv(self):
        """Browse for CSV file"""
        filename = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=os.getcwd()
        )
        if filename:
            self.csv_var.set(filename)


    def update_speed_description(self, event=None):
        """Update speed description label when speed selection changes"""
        speed_map = {
            '高速': '短: 0.2秒 / 長: 0.5秒',
            '中速': '短: 0.3秒 / 長: 1.0秒',
            '低速': '短: 0.5秒 / 長: 1.5秒'
        }
        description = speed_map.get(self.speed_var.get(), '短: 0.2秒 / 長: 0.5秒')
        self.speed_desc_label.config(text=description)

    def on_mode_changed(self):
        """Handle mode change (CSV/GUI mode)"""
        is_csv_mode = self.mode_var.get() == "csv"

        if is_csv_mode:
            # CSV Mode: Prefix/Suffix を無効化（グレーアウト）
            self.prefix_text.config(state="disabled", bg="#f0f0f0")
            self.suffix_text.config(state="disabled", bg="#f0f0f0")
            self.prefix_frame.config(text="Prefix (disabled in CSV Mode)")
            self.suffix_frame.config(text="Suffix (disabled in CSV Mode)")
        else:
            # GUI Mode: Prefix/Suffix を有効化
            self.prefix_text.config(state="normal", bg="white")
            self.suffix_text.config(state="normal", bg="white")
            self.prefix_frame.config(text="Prefix")
            self.suffix_frame.config(text="Suffix")
    
    def get_settings(self) -> dict:
        """Get current settings"""
        # Get prefix/suffix from Text widgets (strip trailing newlines)
        prefix_text = self.prefix_text.get("1.0", tk.END).rstrip('\n')
        suffix_text = self.suffix_text.get("1.0", tk.END).rstrip('\n')

        # 操作速度をSHORT_SLEEP, LONG_SLEEPの値に変換
        speed_map = {
            '高速': {'short': 0.2, 'long': 0.5},
            '中速': {'short': 0.3, 'long': 1.0},
            '低速': {'short': 0.5, 'long': 1.5}
        }
        speed_config = speed_map.get(self.speed_var.get(), speed_map['中速'])

        settings = {
            'csv': self.csv_var.get(),
            'wait': int(self.wait_var.get()) if self.wait_var.get().isdigit() else 60,
            'dry_run': self.dry_run_var.get(),
            'interactive': self.interactive_var.get(),
            'prefix': prefix_text,
            'suffix': suffix_text,
            'short_sleep': speed_config['short'],
            'long_sleep': speed_config['long'],
            'use_csv_mode': self.mode_var.get() == 'csv'  # CSV/GUI モード切り替え
        }

        if self.max_items_var.get().isdigit():
            settings['max_items'] = int(self.max_items_var.get())

        if self.retry_var.get().isdigit():
            settings['retry'] = int(self.retry_var.get())

        return settings
    
    def validate_settings(self) -> bool:
        """Validate settings"""
        csv_file = self.csv_var.get()
        if not csv_file:
            messagebox.showerror("Error", "Please select a CSV file")
            return False
        
        if not Path(csv_file).exists():
            messagebox.showerror("Error", f"CSV file not found: {csv_file}")
            return False
        
        if not self.wait_var.get().isdigit():
            messagebox.showerror("Error", "Wait time must be a number")
            return False
        
        return True
    
    def on_start(self):
        """Start button clicked"""
        if not self.validate_settings():
            return

        self.is_running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_var.set("Starting...")

        if self.on_start_callback:
            self.on_start_callback(self.get_settings())

    def on_stop(self):
        """Stop button clicked"""
        self.is_running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_var.set("Stopping...")

        if self.on_stop_callback:
            self.on_stop_callback()

    def set_callbacks(self, on_start: Callable, on_stop: Callable):
        """Set callback functions"""
        self.on_start_callback = on_start
        self.on_stop_callback = on_stop
    
    def update_progress(self, current: int, total: int):
        """Update progress bar"""
        if total > 0:
            progress = (current / total) * 100
            self.progress_var.set(progress)
            self.status_var.set(f"Processing {current}/{total} ({progress:.1f}%)")
    
    def update_status(self, status: str):
        """Update status"""
        self.status_var.set(status)
    
    def add_log(self, message: str, tag: str = "info"):
        """Add log message"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_line = f"{timestamp} - {message}\n"
        
        self.log_text.insert(tk.END, log_line, tag)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """Clear log"""
        self.log_text.delete(1.0, tk.END)
    
    def on_process_finished(self, exit_code: int, total: int, sent: int, failed: int):
        """Process finished handler"""
        self.is_running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        
        if exit_code == 0:
            status = f"Completed: {sent}/{total} sent, {failed} failed"
            tag = "success" if failed == 0 else "warning"
        else:
            status = f"Error: Process exited with code {exit_code}"
            tag = "error"
        
        self.status_var.set(status)
        self.add_log(status, tag)
    
    def run(self):
        """Run GUI main loop"""
        if self.owns_root:
            self.root.mainloop()
    
    def destroy(self):
        """Destroy GUI"""
        if self.owns_root:
            self.root.destroy()