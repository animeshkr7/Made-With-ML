@echo off
set "SCRIPT_PATH=%~dp0run_pipeline.bat"

echo Setting up Windows Task Scheduler for LinkedIn Monitor...

schtasks /create /f /tn "LinkedInMonitor_0830" /tr "\"%SCRIPT_PATH%\"" /sc daily /st 08:30
schtasks /create /f /tn "LinkedInMonitor_1130" /tr "\"%SCRIPT_PATH%\"" /sc daily /st 11:30
schtasks /create /f /tn "LinkedInMonitor_1430" /tr "\"%SCRIPT_PATH%\"" /sc daily /st 14:30
schtasks /create /f /tn "LinkedInMonitor_1730" /tr "\"%SCRIPT_PATH%\"" /sc daily /st 17:30

echo.
echo Tasks successfully scheduled to run daily at 8:30 AM, 11:30 AM, 2:30 PM, and 5:30 PM!
pause
