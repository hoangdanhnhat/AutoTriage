# Project structure

```
IRTriageCollector/
├── Core/
│   ├── Main-Collector.ps1          # Main orchestration script
│   ├── Config.ps1                   # Configuration settings
│   └── Logger.ps1                   # Logging functions
├── Modules/
│   ├── VolatileData.ps1            # Memory, processes, network
│   ├── RegistryCollection.ps1       # Registry hives
│   ├── EventLogCollection.ps1       # Event logs
│   ├── FileSystemArtifacts.ps1      # Prefetch, MFT, etc.
│   └── ChainOfCustody.ps1          # Documentation & hashing
├── Utils/
│   ├── Compression.ps1              # Archive creation
│   ├── Validation.ps1               # Privilege & space checks
│   └── ExternalTools.ps1            # Third-party tool wrappers
├── Output/
│   └── [timestamp]_[hostname]/      # Collection results
├── Tools/                           # External binaries
│   ├── DumpIt.exe                   # Memory dumper
│   ├── RawCopy.exe                  # Locked file copier
│   └── autorunsc.exe                # Sysinternals tool
├── Logs/                            # Execution logs
├── Reports/                         # HTML/JSON reports
└── README.md                        # Documentation
```

# Phase 1: Project setup & planning

## Step 1.1: Define requirements

List all artifacts to collect:
- Memory dump
- Running processes
- Network connections
- Registry hives
- Event logs
- Prefetch files
- MFT

## Step 1.2: Environment setup

Create project structure:

```powershell
New-Item -ItemType Directory -Path @(
    "IRTriageCollector/Core",
    "IRTriageCollector/Modules",
    "IRTriageCollector/Utils",
    "IRTriageCollector/Tools",
    "IRTriageCollector/Output",
    "IRTriageCollector/Logs",
    "IRTriageCollector/Reports"
)
```

```powershell
git init
```

## Step 1.3: Gather external tools

Download and place in Tools/ folder:

- DumpIt or WinPMEM for memory acquisition
- RawCopy for locked file copying
- Sysinternals tools (optional but recommended)

# Phase 2: Core framework


## Step 2.1: Create configuration file

File: Core/Config.ps1

```powershell
$script:Config = @{
    CollectionName = "IR-Triage-Collection"
    OutputPath = "$PSScriptRoot\..\Output"
    LogPath = "$PSScriptRoot\..\Logs"
    ToolsPath = "$PSScriptRoot\..\Tools"
    
    # Collection toggles
    CollectMemory = $true
    CollectRegistry = $true
    CollectEventLogs = $true
    CollectPrefetch = $true
    CollectNetworkData = $true
    
    # Event log settings
    EventLogsToCollect = @(
        "Security", "System", "Application",
        "Microsoft-Windows-Sysmon/Operational",
        "Microsoft-Windows-PowerShell/Operational"
    )
    
    # Hash algorithm
    HashAlgorithm = "SHA256"
}
```

## Step 2.2: Build logging system

File: Core/Logger.ps1

```powershell
function Write-IRLog {
    param(
        [string]$Message,
        [ValidateSet('Info','Warning','Error','Success')]
        [string]$Level = 'Info'
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Console output with color
    $color = switch($Level) {
        'Info' { 'White' }
        'Warning' { 'Yellow' }
        'Error' { 'Red' }
        'Success' { 'Green' }
    }
    Write-Host $logEntry -ForegroundColor $color
    
    # File output
    $logFile = Join-Path $script:LogPath "IRCollection_$(Get-Date -Format 'yyyyMMdd').log"
    Add-Content -Path $logFile -Value $logEntry
}
```

## Step 2.3: Create validation module

File: Utils/Validation.ps1

```powershell
function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-DiskSpace {
    param([string]$Path, [int]$RequiredGB = 10)
    
    $drive = (Get-Item $Path).PSDrive
    $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
    
    if ($freeSpaceGB -lt $RequiredGB) {
        Write-IRLog "Insufficient disk space: ${freeSpaceGB}GB available, ${RequiredGB}GB required" -Level Error
        return $false
    }
    return $true
}
```

# Phase 3: Volatile data collection

## Step 3.1: Memory dump module

File: Modules/VolatileData.ps1

```powershell
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
```

## Step 3.2: Running processes \ NOTE: maybe don't need?

File: Modules/VolatileData.ps1

```powershell
function Get-ProcessList {
    param([string]$OutputPath)
    
    Write-IRLog "Collecting running processes..."
    
    $processes = Get-Process | Select-Object Name, Id, Path, Company, 
        ProductVersion, StartTime, @{N='ParentProcessId';E={$_.ParentId}},
        @{N='CommandLine';E={(Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)').CommandLine}}
    
    # Export to multiple formats
    $processes | Export-Csv -Path (Join-Path $OutputPath "processes.csv") -NoTypeInformation
    $processes | ConvertTo-Json | Out-File -FilePath (Join-Path $OutputPath "processes.json")
    
    return $processes
}
```

## Step 3.3: Network connections

```powershell
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
```

# Phase 4: Registry collection

## Step 4.1: Registry hives

```powershell
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
```

