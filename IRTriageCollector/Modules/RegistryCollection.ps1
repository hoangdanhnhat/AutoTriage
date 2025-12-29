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
    
    $rawCopy = Join-Path $script:Config.ToolsPath "RawCopy.exe"
    
    foreach ($hive in $hives.GetEnumerator()) {
        try {
            if (Test-Path $rawCopy) {
                # Use RawCopy for locked files
                # RawCopy syntax: /FileNamePath:<source> /OutputPath:<destination_directory>
                Start-Process -FilePath $rawCopy -ArgumentList "/FileNamePath:$($hive.Value) /OutputPath:$regPath" -Wait -NoNewWindow
            } else {
                # Fallback: reg save command
                $destination = Join-Path $regPath "$($hive.Key)"
                reg save "HKLM\$($hive.Key)" "$destination" /y | Out-Null
            }
            
            Write-IRLog "Collected $($hive.Key) hive" -Level Success
        } catch {
            Write-IRLog "Failed to collect $($hive.Key): $_" -Level Error
        }
    }
}

function Get-UserRegistryHives {
    param([string]$OutputPath)
    
    Write-IRLog "Collecting user registry hives..." -Level Info
    
    # Collect NTUSER.DAT from user profiles
    $userProfiles = Get-ChildItem "C:\Users" -Directory -ErrorAction SilentlyContinue
    
    foreach ($profile in $userProfiles) {
        $ntuserPath = Join-Path $profile.FullName "NTUSER.DAT"
        if (Test-Path $ntuserPath) {
            try {
                $destination = Join-Path $OutputPath "NTUSER_$($profile.Name).DAT"
                Copy-Item -Path $ntuserPath -Destination $destination -ErrorAction Stop
                Write-IRLog "Collected NTUSER.DAT for $($profile.Name)" -Level Success
            } catch {
                Write-IRLog "Failed to collect NTUSER.DAT for $($profile.Name): $_" -Level Warning
            }
        }
    }
}