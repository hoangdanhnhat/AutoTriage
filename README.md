# AutoTriage - IR Triage Collection Tool

An automated Incident Response (IR) triage collection tool for Windows systems that collects volatile and non-volatile forensic artifacts.

## Features

- **Memory Dump**: Captures system memory (requires DumpIt.exe in Tools folder)
- **Volatile Data**: Running processes, network connections
- **Registry Hives**: System and user registry hives
- **Event Logs**: Security, System, Application, and other critical logs
- **File System Artifacts**: Prefetch files, startup items, scheduled tasks
- **Chain of Custody**: Automated documentation with file hashes
- **Compression**: Automatic ZIP archive creation

## Prerequisites

- **Windows OS** (tested on Windows 10/11)
- **PowerShell 5.1+**
- **Administrator Privileges** (required)

## Quick Start

### 1. Open PowerShell as Administrator

Press `Win + X` and select "Windows PowerShell (Admin)" or "Terminal (Admin)"

### 2. Navigate to the Core Directory

```powershell
cd "d:\Personal Project\AutoTriage\IRTriageCollector\Core"
```

### 3. Set Execution Policy (if needed)

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

### 4. Run the Collector

**Basic usage:**
```powershell
.\MainCollector.ps1
```

**Skip memory collection (faster):**
```powershell
.\MainCollector.ps1 -SkipMemory
```

**Custom output location:**
```powershell
.\MainCollector.ps1 -OutputLocation "D:\Evidence"
```

**Quick mode:**
```powershell
.\MainCollector.ps1 -QuickMode
```

**Combine parameters:**
```powershell
.\MainCollector.ps1 -SkipMemory -OutputLocation "D:\Evidence"
```

## Output

The tool creates a timestamped directory containing:

```
Output/
└── [timestamp]_[hostname]/
    ├── ChainOfCustody.json          # Collection metadata & file hashes
    ├── processes.csv                # Running processes
    ├── processes.json               # Running processes (JSON)
    ├── network_connections.csv      # Active network connections
    ├── listening_ports.csv          # Listening ports
    ├── Registry/                    # Registry hives
    │   ├── SAM
    │   ├── SECURITY
    │   ├── SOFTWARE
    │   ├── SYSTEM
    │   └── DEFAULT
    ├── EventLogs/                   # Event log files
    │   ├── Security.evtx
    │   ├── System.evtx
    │   └── ...
    ├── Prefetch/                    # Prefetch files
    └── Startup/                     # Startup items & services
        ├── scheduled_tasks.csv
        └── services.csv
```

A ZIP archive is automatically created after collection completes.

## Configuration

Edit `Core/Config.ps1` to customize:

- Output paths
- Collection toggles (enable/disable specific modules)
- Event logs to collect
- Hash algorithm

## External Tools (Optional)

Place these tools in the `Tools/` directory for enhanced functionality:

- **DumpIt.exe** or **WinPMEM** - Memory acquisition
- **RawCopy.exe** - Copy locked files
- **autorunsc.exe** - Sysinternals autorun analysis

## Logs

Execution logs are saved to: `IRTriageCollector/Logs/IRCollection_[date].log`

## System Requirements

- **Disk Space**: Minimum 10GB free space (checked automatically)
- **Memory**: Varies based on system RAM (for memory dumps)

## Troubleshooting

### "Execution Policy" Error

Run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

### "Access Denied" Errors

Ensure you're running PowerShell as Administrator.

### Missing Module Errors

Ensure all files in the following directories exist:
- `Core/` - Config.ps1, Logger.ps1, MainCollector.ps1
- `Utils/` - Validation.ps1
- `Modules/` - All .ps1 files

## Collection Order (by Volatility)

1. Memory dump (most volatile)
2. Running processes & network connections
3. Registry hives
4. Event logs
5. File system artifacts (least volatile)

## Security Notes

- This tool requires administrator privileges
- Collected data may contain sensitive information
- Maintain proper chain of custody
- Store collected evidence securely

## License

This tool is for authorized incident response and forensic investigations only.

## Author

Created for incident response and digital forensics purposes.
