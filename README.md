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
- **Ansible Deployment**: Remote deployment and execution on multiple Windows hosts

## Prerequisites

- **Windows OS** (tested on Windows 10/11)
- **PowerShell 5.1+**
- **Administrator Privileges** (required)
- **Ansible** (optional, for remote deployment)

## Quick Start

### Option 1: Local Execution

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

### Option 2: Remote Deployment with Ansible

For deploying and executing on multiple Windows hosts remotely:

#### Prerequisites (on Ansible control machine)
- Ansible 2.9+

#### Setup

```bash
# Navigate to ansible directory
cd Ansible

# Edit inventory file to add your Windows hosts
nano inventory
```

Configure your Windows targets in the `[windows_server]` section

**Note**: For security, use Ansible vault or SSH keys instead of plaintext passwords in production.

#### Execute

```bash
# Test connectivity to Windows hosts
ansible windows_server -i inventory -m win_ping

# Deploy and execute AutoTriage on all hosts
ansible-playbook -i inventory auto-triage.yml
```

#### Playbook Features
- Validates connectivity to all target hosts
- Excludes Tools folder from Windows Defender (prevents false positives)
- Deploys AutoTriage to remote systems
- Executes the collection script
- Automatically fetches generated artifacts back to control machine
- Cleans up temporary files on remote hosts
- Collects both ZIP archives and log files


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

### Local Execution

Edit `Core/Config.ps1` to customize:

- Output paths
- Collection toggles (enable/disable specific modules)
- Event logs to collect
- Hash algorithm

### Ansible Deployment

The main playbook configuration is in `Ansible/auto-triage.yml`:

- **remote_temp_path**: Working directory on target hosts (default: `C:\temp_triage`)
- **local_artifact_dir**: Where retrieved artifacts are stored (default: `./fetched_artifacts`)
- **hosts**: Target host group (default: `windows_server`)

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

### Local Execution

#### "Execution Policy" Error

Run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

#### "Access Denied" Errors

Ensure you're running PowerShell as Administrator.

#### Missing Module Errors

Ensure all files in the following directories exist:
- `Core/` - Config.ps1, Logger.ps1, MainCollector.ps1
- `Utils/` - Validation.ps1
- `Modules/` - All .ps1 files

### Ansible Deployment

#### "unreachable" or authentication failures

- Verify Windows hosts are accessible from control machine
- Confirm `ansible_user` and `ansible_password` are correct
- Ensure ports 5985 (HTTP) or 5986 (HTTPS) are open on Windows hosts
- Check that target hosts have WinRM enabled (run on target as admin):
  ```powershell
  Enable-PSRemoting -Force
  ```

#### "pywinrm" not found error

Install the required Python package on your Ansible control machine:
```bash
pip install pywinrm
```

#### Playbook hangs on win_ping

- Check WinRM listener status on target: `winrm get winrm/config/listener`
- Try connecting directly: `ansible windows_server -i inventory -m win_ping -vvv`

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
