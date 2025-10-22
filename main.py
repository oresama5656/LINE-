#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LINE Stamp Maker - Main Entry Point
統合LINEスタンプ作成ツール
"""

import sys
from pathlib import Path

# モジュールパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from gui.main_window import StampMakerGUI


def main():
    """メイン関数"""
    try:
        # GUIを起動
        app = StampMakerGUI()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
