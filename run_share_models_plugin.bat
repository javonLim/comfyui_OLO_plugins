@echo off

REM 快速运行share_models_simple.py的批处理脚本
chcp 65001 > nul
cd /d "%~dp0"
python share_models_simple.py
pause
