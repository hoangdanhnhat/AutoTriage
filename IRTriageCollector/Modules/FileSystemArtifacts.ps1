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
    # Collect autoruns, scheduled tasks, services
}

function Get-RecentFiles {
    param([string]$OutputPath)
    # Collect recent files, jump lists, LNK files
}