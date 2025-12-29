function Get-PrefetchFiles {
    param([string]$OutputPath)
    
    Write-IRLog "Collecting Prefetch files..."
    
    $prefetchPath = Join-Path $OutputPath "Prefetch"
    New-Item -ItemType Directory -Path $prefetchPath -Force | Out-Null
    
    $source = "C:\Windows\Prefetch\*.pf"
    
    try {
        Copy-Item -Path $source -Destination $prefetchPath -ErrorAction Stop
        $count = (Get-ChildItem $prefetchPath).Count
        Write-IRLog "Collected $count prefetch files" -Level Success
    } catch {
        Write-IRLog "Failed to collect prefetch files: $_" -Level Error
    }
}

function Get-BrowserHistory {
    param([string]$OutputPath)
    # Collect browser history, downloads, cookies
}

function Get-StartupItems {
    param([string]$OutputPath)
    
    Write-IRLog "Collecting startup items..." -Level Info
    
    $startupPath = Join-Path $OutputPath "Startup"
    New-Item -ItemType Directory -Path $startupPath -Force | Out-Null
    
    # Collect scheduled tasks
    try {
        Get-ScheduledTask | Select-Object TaskName, TaskPath, State, Author, Description |
            Export-Csv -Path (Join-Path $startupPath "scheduled_tasks.csv") -NoTypeInformation
        Write-IRLog "Collected scheduled tasks" -Level Success
    } catch {
        Write-IRLog "Failed to collect scheduled tasks: $_" -Level Warning
    }
    
    # Collect services
    try {
        Get-Service | Select-Object Name, DisplayName, Status, StartType, ServiceType |
            Export-Csv -Path (Join-Path $startupPath "services.csv") -NoTypeInformation
        Write-IRLog "Collected services" -Level Success
    } catch {
        Write-IRLog "Failed to collect services: $_" -Level Warning
    }
}

function Get-RecentFiles {
    param([string]$OutputPath)
    # Collect recent files, jump lists, LNK files
}