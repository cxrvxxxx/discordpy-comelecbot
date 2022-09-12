@echo off
:loop
CLS
%~dp0\.venv\scripts\python.exe -m bot
TIMEOUT /t 5
GOTO loop
PAUSE