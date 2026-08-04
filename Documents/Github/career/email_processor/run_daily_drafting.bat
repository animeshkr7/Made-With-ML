@echo off
set PYTHONIOENCODING=utf-8
cd /d "c:\Users\aks\Documents\Github\career\email_processor"
call python daily_email_drafting.py > drafting_log.txt 2>&1
call python send_notification.py >> drafting_log.txt 2>&1
