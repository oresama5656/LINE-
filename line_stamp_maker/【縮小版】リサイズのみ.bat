@echo off
chcp 65001 >nul
echo ========================================
echo  LINEスタンプ用リサイズツール（縮小版）
echo ========================================
echo.
echo base/ フォルダの画像を370×320pxにリサイズします
echo （テキスト合成なし・全体表示・余白あり）
echo.
node resize-only.js
echo.
pause
