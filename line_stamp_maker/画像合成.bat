@echo off
chcp 65001 >nul
echo ========================================
echo   LINEスタンプ画像合成ツール
echo ========================================
echo.
echo base/ と text/ フォルダの画像を組み合わせます
echo.
node combine.js
echo.
pause
