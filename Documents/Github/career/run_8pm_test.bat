@echo off
setlocal
cd /d "c:\Users\aks\Documents\Github\career"
"C:\Users\aks\.pyenv\pyenv-win\versions\3.10.10\python.exe" "c:\Users\aks\Documents\Github\career\.agents\skills\linkedin-job-hunt\scripts\run_linkedin_hunt.py" --hours 1 >> "c:\Users\aks\Documents\Github\career\.agents\skills\linkedin-job-hunt\logs\task_8pm_test.log" 2>&1
endlocal
