#!/bin/bash
# ChatGPT Prefix ツール起動用（Mac用 .command 版）

cd "$(dirname "$0")"
python3 -m chatgpt_prefix.gui_launcher

echo
echo "✅ ChatGPT Prefix が終了しました。ウィンドウを閉じてOKです。"
read -p "Enterキーを押すと閉じます..."
