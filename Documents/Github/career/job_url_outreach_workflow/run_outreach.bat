@echo off
set PYTHONIOENCODING=utf-8
cd /d "c:\Users\aks\Documents\Github\career"

echo ================================================== >> job_url_outreach_workflow\outreach_log.txt
echo Running Workflow at %date% %time% >> job_url_outreach_workflow\outreach_log.txt
echo ================================================== >> job_url_outreach_workflow\outreach_log.txt

call python job_url_outreach_workflow\main.py >> job_url_outreach_workflow\outreach_log.txt 2>&1
