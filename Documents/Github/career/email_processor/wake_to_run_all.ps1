$tasks = Get-ScheduledTask | Where-Object { $_.TaskName -match 'LinkedInMonitor' }

foreach ($task in $tasks) {
    Write-Host "Updating task: $($task.TaskName)"
    $settings = $task.Settings
    $settings.WakeToRun = $true
    Set-ScheduledTask -TaskName $task.TaskName -Settings $settings
}
Write-Host "All tasks updated successfully."
