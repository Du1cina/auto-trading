@echo off
start "交易引擎" cmd /k "python 01.engine.py"
start "Web面板" cmd /k "python web/app.py"