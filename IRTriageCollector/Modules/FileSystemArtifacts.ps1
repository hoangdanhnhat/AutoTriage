function Get-ProgramDataArtifacts {
    param([string]$OutputPath)
    
    Write-IRLog "Collecting ProgramData artifacts..." -Level Info
    
    $programDataBasePath = Join-Path $OutputPath "ProgramData"
    New-Item -ItemType Directory -Path $programDataBasePath -Force | Out-Null
    
    # Define specific paths to collect
    $paths = @(
        @{Source = "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp"; Dest = "StartUp"; Desc = "Startup items" },
        @{Source = "C:\ProgramData\Microsoft\Windows\WER"; Dest = "WER"; Desc = "Windows Error Reporting" },
        @{Source = "C:\ProgramData\Microsoft\Windows Defender\Scans\History"; Dest = "DefenderHistory"; Desc = "Windows Defender scan history" }
    )
    
    foreach ($path in $paths) {
        if (Test-Path $path.Source) {
            try {
                $destPath = Join-Path $programDataBasePath $path.Dest
                New-Item -ItemType Directory -Path $destPath -Force | Out-Null
                
                Copy-Item -Path "$($path.Source)\*" -Destination $destPath -Recurse -Force -ErrorAction SilentlyContinue
                $count = (Get-ChildItem $destPath -Recurse -File -ErrorAction SilentlyContinue).Count
                Write-IRLog "Collected $count files from $($path.Desc)" -Level Success
            }
            catch {
                Write-IRLog "Failed to collect $($path.Desc): $_" -Level Warning
            }
        }
        else {
            Write-IRLog "Path not found: $($path.Source)" -Level Warning
        }
    }
    
    # Collect application-specific folders (AnyDesk, TeamViewer, VPNs, etc.)
    Write-IRLog "Scanning for 3rd party application artifacts..." -Level Info
    
    $interestingApps = @('AnyDesk', 'TeamViewer', 'LogMeIn', 'Cisco', 'OpenVPN', 'NordVPN', 'ExpressVPN', 'Slack', 'Discord', 'Zoom')
    
    foreach ($app in $interestingApps) {
        $appPath = Join-Path "C:\ProgramData" $app
        if (Test-Path $appPath) {
            try {
                $destPath = Join-Path $programDataBasePath "ThirdParty\$app"
                New-Item -ItemType Directory -Path $destPath -Force | Out-Null
                
                Copy-Item -Path "$appPath\*" -Destination $destPath -Recurse -Force -ErrorAction SilentlyContinue
                $count = (Get-ChildItem $destPath -Recurse -File -ErrorAction SilentlyContinue).Count
                if ($count -gt 0) {
                    Write-IRLog "Collected $count files from $app" -Level Success
                }
            }
            catch {
                Write-IRLog "Failed to collect $app data: $_" -Level Warning
            }
        }
    }
}

function Get-UserArtifacts {
    param([string]$OutputPath)
    
    Write-IRLog "Collecting user profile artifacts..." -Level Info
    
    $usersBasePath = Join-Path $OutputPath "Users"
    New-Item -ItemType Directory -Path $usersBasePath -Force | Out-Null
    
    # Get all user profiles
    $userProfiles = Get-ChildItem "C:\Users" -Directory -ErrorAction SilentlyContinue | 
    Where-Object { $_.Name -notin @('Public', 'Default', 'Default User', 'All Users') }
    
    foreach ($userProfile in $userProfiles) {
        $userName = $userProfile.Name
        Write-IRLog "Collecting artifacts for user: $userName" -Level Info
        
        $userDestPath = Join-Path $usersBasePath $userName
        New-Item -ItemType Directory -Path $userDestPath -Force | Out-Null
        
        # Define user-specific paths to collect
        $userPaths = @(
            @{Source = "AppData\Roaming\Microsoft\Windows\Recent"; Dest = "Recent"; Desc = "Recent files" },
            @{Source = "AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine"; Dest = "PSReadLine"; Desc = "PowerShell history" },
            @{Source = "AppData\Local\Microsoft\Windows\Explorer"; Dest = "Explorer"; Desc = "Explorer data" },
            @{Source = "AppData\Local\ConnectedDevicesPlatform"; Dest = "ConnectedDevicesPlatform"; Desc = "Connected devices" },
            @{Source = "AppData\Local\Google\Chrome\User Data\Default"; Dest = "Chrome"; Desc = "Chrome browser data" },
            @{Source = "AppData\Local\Microsoft\Edge\User Data\Default"; Dest = "Edge"; Desc = "Edge browser data" },
            @{Source = "AppData\Roaming\Mozilla\Firefox\Profiles"; Dest = "Firefox"; Desc = "Firefox browser data" }
        )
        
        foreach ($path in $userPaths) {
            $sourcePath = Join-Path $userProfile.FullName $path.Source
            
            if (Test-Path $sourcePath) {
                try {
                    $destPath = Join-Path $userDestPath $path.Dest
                    
                    if ($path.IsFile) {
                        # Copy single file
                        New-Item -ItemType Directory -Path (Split-Path $destPath -Parent) -Force | Out-Null
                        Copy-Item -Path $sourcePath -Destination $destPath -Force -ErrorAction SilentlyContinue
                        if (Test-Path $destPath) {
                            Write-IRLog "Collected $($path.Desc) for $userName" -Level Success
                        }
                    }
                    else {
                        # Copy directory
                        New-Item -ItemType Directory -Path $destPath -Force | Out-Null
                        Copy-Item -Path "$sourcePath\*" -Destination $destPath -Recurse -Force -ErrorAction SilentlyContinue
                        $count = (Get-ChildItem $destPath -Recurse -File -ErrorAction SilentlyContinue).Count
                        if ($count -gt 0) {
                            Write-IRLog "Collected $count files from $($path.Desc) for $userName" -Level Success
                        }
                    }
                }
                catch {
                    Write-IRLog "Failed to collect $($path.Desc) for $userName : $_" -Level Warning
                }
            }
        }
    }
}

function Get-WindowsArtifacts {
    param([string]$OutputPath)
    
    Write-IRLog "Collecting Windows directory artifacts..." -Level Info
    
    $windowsBasePath = Join-Path $OutputPath "Windows"
    New-Item -ItemType Directory -Path $windowsBasePath -Force | Out-Null
    
    $rawCopy = Join-Path $script:Config.ToolsPath "RawCopy.exe"
    
    # Define specific paths to collect
    $paths = @(
        @{Source = "C:\Windows\System32\winevt\Logs"; Dest = "System32\winevt\Logs"; Desc = "Event logs" },
        @{Source = "C:\Windows\Prefetch"; Dest = "Prefetch"; Desc = "Prefetch files" },
        @{Source = "C:\Windows\AppCompat\Programs"; Dest = "AppCompat\Programs"; Desc = "AppCompat data"; HasLockedFiles = $true },
        @{Source = "C:\Windows\Tasks"; Dest = "Tasks"; Desc = "Scheduled tasks" },
        @{Source = "C:\Windows\System32\drivers\etc"; Dest = "System32\drivers\etc"; Desc = "Hosts file and network config" }
    )
    
    foreach ($path in $paths) {
        if (Test-Path $path.Source) {
            try {
                $destPath = Join-Path $windowsBasePath $path.Dest
                New-Item -ItemType Directory -Path $destPath -Force | Out-Null
                
                # Special handling for AppCompat (contains locked Amcache.hve)
                if ($path.HasLockedFiles -and (Test-Path $rawCopy)) {
                    # Copy Amcache.hve using RawCopy
                    $amcachePath = Join-Path $path.Source "Amcache.hve"
                    if (Test-Path $amcachePath) {
                        Start-Process -FilePath $rawCopy -ArgumentList "/FileNamePath:`"$amcachePath`" /OutputPath:`"$destPath`"" -Wait -NoNewWindow -ErrorAction SilentlyContinue
                    }
                    
                    # Copy other files normally
                    Get-ChildItem -Path $path.Source -File -ErrorAction SilentlyContinue | 
                    Where-Object { $_.Name -ne "Amcache.hve" } | 
                    ForEach-Object {
                        Copy-Item -Path $_.FullName -Destination $destPath -Force -ErrorAction SilentlyContinue
                    }
                }
                else {
                    # Regular copy for other directories
                    Copy-Item -Path "$($path.Source)\*" -Destination $destPath -Recurse -Force -ErrorAction SilentlyContinue
                }
                
                $count = (Get-ChildItem $destPath -Recurse -File -ErrorAction SilentlyContinue).Count
                Write-IRLog "Collected $count files from $($path.Desc)" -Level Success
            }
            catch {
                Write-IRLog "Failed to collect $($path.Desc): $_" -Level Warning
            }
        }
        else {
            Write-IRLog "Path not found: $($path.Source)" -Level Warning
        }
    }
}