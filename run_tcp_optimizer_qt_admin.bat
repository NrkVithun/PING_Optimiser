@echo off
:: Change to the script directory
cd /d "%~dp0"

:: Check if the script is running with admin privileges
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo Requesting administrative privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /B
)

:: Run the Python script
python "tcp_optimizer_qt.py"
pause