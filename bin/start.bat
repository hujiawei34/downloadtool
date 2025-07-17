@echo off
REM 设置编码为UTF-8
chcp 65001
cd /d %~dp0..\src\python
echo 当前目录：%cd%
REM 如果有虚拟环境请取消下一行注释
call ..\..\..\.venv\Scripts\activate.bat
echo 虚拟环境：%VIRTUAL_ENV%
python app.py
pause