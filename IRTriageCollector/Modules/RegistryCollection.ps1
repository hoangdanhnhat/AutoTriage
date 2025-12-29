function Get-RegistryHives {
    param([string]$OutputPath)
    
    Write-IRLog "Collecting registry hives..."
    
    $regPath = Join-Path $OutputPath "Registry"
    New-Item -ItemType Directory -Path $regPath -Force | Out-Null
    
    # Define critical registry hives
    $hives = @{
        'SAM' = 'C:\Windows\System32\config\SAM'
        'SECURITY' = 'C:\Windows\System32\config\SECURITY'
        'SOFTWARE' = 'C:\Windows\System32\config\SOFTWARE'
        'SYSTEM' = 'C:\Windows\System32\config\SYSTEM'
        'DEFAULT' = 'C:\Windows\System32\config\DEFAULT'
    }
    
    $rawCopy = Join-Path $script:ToolsPath "RawCopy.exe"
    
    foreach ($hive in $hives.GetEnumerator()) {
        try {
            $destination = Join-Path $regPath "$($hive.Key)"
            
            if (Test-Path $rawCopy) {
                # Use RawCopy for locked files
                Start-Process -FilePath $rawCopy -ArgumentList "/FileNamePath:$($hive.Value) /OutputPath:$destination" -Wait -NoNewWindow
            } else {
                # Fallback: reg save command
                reg save "HKLM\$($hive.Key)" "$destination" /y | Out-Null
            }
            
            Write-IRLog "Collected $($hive.Key) hive" -Level Success
        } catch {
            Write-IRLog "Failed to collect $($hive.Key): $_" -Level Error
        }
    }
    
    # Also collect user hives
    Get-UserRegistryHives -OutputPath $regPath
}