$tasks = @('NaukriProfileUpdater', 'CareerMonitor')
foreach ($task in $tasks) {
    try {
        $wake = (Get-ScheduledTask -TaskName $task -ErrorAction Stop).Settings.WakeToRun
        Write-Host "$task WakeToRun: $wake"
    } catch {
        Write-Host "Task $task not found."
    }
}
