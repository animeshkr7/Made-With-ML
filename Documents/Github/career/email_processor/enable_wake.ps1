$tasks = @("LinkedInMonitor_0830", "LinkedInMonitor_1130", "LinkedInMonitor_1430", "LinkedInMonitor_1730")

foreach ($taskName in $tasks) {
    # Get current task settings
    $task = Get-ScheduledTask -TaskName $taskName
    
    # Update settings to wake computer
    $task.Settings.WakeToRun = $true
    
    # Apply settings
    Set-ScheduledTask -TaskName $taskName -Settings $task.Settings
    Write-Host "Updated $taskName to Wake the computer"
}
