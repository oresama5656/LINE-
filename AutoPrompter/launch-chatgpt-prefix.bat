@echo off
if not defined IS_MINIMIZED set IS_MINIMIZED=1 && start "" /min "%~f0" %* && exit
chcp 65001 > nul
REM AutoPrompter - ChatGPT Prefix画像作成ツール起動

cd /d "%~dp0"
pythonw -m chatgpt_prefix.gui_launcher

if errorlevel 1 (
    echo.
    echo [ERROR] ChatGPT Prefix起動に失敗しました
    echo Pythonがインストールされているか確認してください
    echo.
    pause
) else (
    echo.
    echo [SUCCESS] ChatGPT Prefix終了
)
