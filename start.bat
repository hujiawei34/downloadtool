@echo off
cd /d %~dp0src\python
REM 如果有虚拟环境请取消下一行注释
REM call ..\..\venv\Scripts\activate.bat
python app.py
pause 