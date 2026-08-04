$task = Get-ScheduledTask -TaskName "CareerMonitor"
$task.Settings.WakeToRun = $true
Set-ScheduledTask -TaskName "CareerMonitor" -Settings $task.Settings
Write-Host "CareerMonitor has been updated to wake the computer from sleep!"
