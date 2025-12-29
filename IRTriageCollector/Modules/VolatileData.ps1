function Get-MemoryDump {
    param([string]$OutputPath)
    
    Write-IRLog "Starting memory acquisition..."
    
    $memoryFile = Join-Path $OutputPath "memory.dmp"
    $dumper = Join-Path $script:ToolsPath "DumpIt.exe"
    
    if (Test-Path $dumper) {
        # Execute memory dumper
        Start-Process -FilePath $dumper -ArgumentList "/O $memoryFile /Q" -Wait -NoNewWindow
        
        if (Test-Path $memoryFile) {
            $hash = Get-FileHash -Path $memoryFile -Algorithm SHA256
            Write-IRLog "Memory dump completed: $($hash.Hash)" -Level Success
            return @{
                FilePath = $memoryFile
                Hash = $hash.Hash
                Size = (Get-Item $memoryFile).Length
            }
        }
    } else {
        Write-IRLog "Memory dumper not found, skipping..." -Level Warning
    }
}

function Get-NetworkConnections {
    param([string]$OutputPath)
    
    Write-IRLog "Collecting network connections..."
    
    $connections = Get-NetTCPConnection | Select-Object LocalAddress, LocalPort,
        RemoteAddress, RemotePort, State, OwningProcess,
        @{N='ProcessName';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name}},
        @{N='ProcessPath';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Path}}
    
    $connections | Export-Csv -Path (Join-Path $OutputPath "network_connections.csv") -NoTypeInformation
    
    # Also collect listening ports
    Get-NetTCPConnection -State Listen | Export-Csv -Path (Join-Path $OutputPath "listening_ports.csv") -NoTypeInformation
    
    Write-IRLog "Network data collected" -Level Success
}