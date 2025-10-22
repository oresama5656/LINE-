@echo off
chcp 65001 >nul
echo ========================================
echo   LINEスタンプ main/tab 作成（縮小版）
echo ========================================
echo.
echo ※画像全体が見えるよう縮小して調整します
echo.
node select-main-tab-fit.js
echo.
pause
