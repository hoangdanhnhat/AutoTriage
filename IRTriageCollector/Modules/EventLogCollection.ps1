function Get-EventLogsCollection {
    param([string]$OutputPath)
    
    Write-IRLog "Collecting event logs..."
    
    $evtxPath = Join-Path $OutputPath "EventLogs"
    New-Item -ItemType Directory -Path $evtxPath -Force | Out-Null
    
    foreach ($logName in $script:Config.EventLogsToCollect) {
        try {
            $log = Get-WinEvent -ListLog $logName -ErrorAction Stop
            $fileName = $logName -replace '/', '-'
            $destination = Join-Path $evtxPath "$fileName.evtx"
            
            # Export event log
            wevtutil epl $logName $destination
            
            if (Test-Path $destination) {
                Write-IRLog "Collected $logName" -Level Success
            }
        } catch {
            Write-IRLog "Failed to collect $logName : $_" -Level Warning
        }
    }
}