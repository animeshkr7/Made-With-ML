$taskName = 'LinkedInMonitor_Test_0916'
$task = Get-ScheduledTask -TaskName $taskName
$settings = $task.Settings
$settings.WakeToRun = $true
Set-ScheduledTask -TaskName $taskName -Settings $settings
