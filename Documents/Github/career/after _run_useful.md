# Check logs after a run
type c:\Users\aks\Documents\Github\career\monitor\monitor_log.txt

# Manually trigger it right now
schtasks /run /tn "CareerMonitor"

# Delete if you ever want to remove it
schtasks /delete /tn "CareerMonitor" /f
