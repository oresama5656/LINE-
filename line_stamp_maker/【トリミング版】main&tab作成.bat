@echo off
chcp 65001 >nul
echo ========================================
echo  LINEスタンプ main/tab 作成（トリミング版）
echo ========================================
echo.
echo ※中央部分を切り抜いてサイズぴったりに調整します
echo.
node select-main-tab-trimming.js
echo.
pause
