@echo off
REM Get the directory of this batch file
set "DIR=%~dp0"
cd /d "%DIR%"

REM Wait 60 seconds to ensure Wi-Fi is connected if waking from sleep
timeout /t 60 /nobreak > NUL


echo ========================================= >> pipeline.log
echo Starting LinkedIn Monitor Pipeline at %date% %time% >> pipeline.log
python run_pipeline.py >> pipeline.log 2>&1
echo Pipeline execution finished at %date% %time% >> pipeline.log
