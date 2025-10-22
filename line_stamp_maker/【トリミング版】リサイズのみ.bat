@echo off
chcp 65001 >nul
echo ========================================
echo LINEスタンプ用リサイズツール（トリミング版）
echo ========================================
echo.
echo base/ フォルダの画像を370×320pxにリサイズします
echo （テキスト合成なし・中央切り抜き・余白なし）
echo.
node resize-only-trimming.js
echo.
pause
