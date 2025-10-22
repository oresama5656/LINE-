#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for main/tab creation using Python method
"""

from pathlib import Path
from modules.image_resizer import ImageResizer

def test_main_tab_creation():
    # Test with the last processed resized folder
    test_folder = Path("C:/Users/oresa/Downloads/スタンプ/stamp_20251022_235004/resized")

    if not test_folder.exists():
        print(f"❌ Test folder not found: {test_folder}")
        return False

    # Check if resized images exist
    png_files = list(test_folder.glob('*.png'))
    print(f"Found {len(png_files)} PNG files in {test_folder}")

    if len(png_files) == 0:
        print("❌ No PNG files found")
        return False

    # Create ImageResizer instance
    line_stamp_maker = Path("D:/LINEスタンプツール/line_stamp_maker")
    resizer = ImageResizer(str(line_stamp_maker))

    # Test main/tab creation with default indices (1, 1)
    print("\nTesting main/tab creation with main=1, tab=1...")
    success = resizer.create_main_tab_python(
        test_folder,
        test_folder,
        main_index=1,
        tab_index=1,
        mode='fit',
        progress_callback=None  # Skip callback to avoid encoding issues in test
    )

    if success:
        print("\nTest successful!")
        main_path = test_folder / "main.png"
        tab_path = test_folder / "tab.png"
        print(f"  main.png exists: {main_path.exists()}")
        print(f"  tab.png exists: {tab_path.exists()}")
    else:
        print("\nTest failed!")

    return success

if __name__ == "__main__":
    test_main_tab_creation()
