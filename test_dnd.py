#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ドラッグ&ドロップ機能のテストスクリプト
"""

import sys
from pathlib import Path

# モジュールパスを追加
sys.path.insert(0, str(Path(__file__).parent))

try:
    from tkinterdnd2 import TkinterDnD
    print("✅ tkinterdnd2 is installed and working!")
    print(f"   Version: {TkinterDnD.__version__ if hasattr(TkinterDnD, '__version__') else 'unknown'}")

    # 簡易テスト
    root = TkinterDnD.Tk()
    root.title("Drag & Drop Test")
    root.geometry("400x200")

    import tkinter as tk
    from tkinterdnd2 import DND_FILES

    label = tk.Label(
        root,
        text="ここにフォルダをドラッグ&ドロップしてください",
        bg="#f0f0f0",
        relief="solid",
        borderwidth=2,
        padx=20,
        pady=40
    )
    label.pack(fill="both", expand=True, padx=20, pady=20)

    def on_drop(event):
        dropped = event.data.strip('{}')
        label.config(text=f"ドロップされたパス:\n{dropped}")
        print(f"Dropped: {dropped}")

    label.drop_target_register(DND_FILES)
    label.dnd_bind('<<Drop>>', on_drop)

    print("\n🖱️  テストウィンドウが開きます。")
    print("   フォルダをウィンドウにドラッグ&ドロップしてください。")
    print("   ウィンドウを閉じるとテスト終了です。\n")

    root.mainloop()

except ImportError as e:
    print("❌ tkinterdnd2 is NOT installed!")
    print(f"   Error: {e}")
    print("\n📦 Install with:")
    print("   pip install tkinterdnd2")
    sys.exit(1)
