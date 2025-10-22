@echo off
echo.
echo WebP to PNG Converter
echo.
powershell.exe -ExecutionPolicy Bypass -File "%~dp0convert-webp-to-png.ps1"
echo.
pause
