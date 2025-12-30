param(
    [string]$OutputLocation,
    [switch]$SkipMemory,
    [switch]$QuickMode
)

# Import all modules
. "$PSScriptRoot\Config.ps1"
. "$PSScriptRoot\Logger.ps1"
. "$PSScriptRoot\..\Utils\Validation.ps1"
. "$PSScriptRoot\..\Modules\VolatileData.ps1"
. "$PSScriptRoot\..\Modules\RegistryCollection.ps1"
. "$PSScriptRoot\..\Modules\FileSystemArtifacts.ps1"
. "$PSScriptRoot\..\Modules\ChainOfCustody.ps1"

function Start-IRCollection {
    Write-Host "`n=== IR Triage Collection Tool ===" -ForegroundColor Cyan
    Write-Host "Starting collection at $(Get-Date)`n"
    
    # Pre-flight checks
    if (-not (Test-Administrator)) {
        Write-IRLog "This script requires administrator privileges!" -Level Error
        exit 1
    }
    
    # Create output directory
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $collectionPath = Join-Path $script:Config.OutputPath "${timestamp}_$env:COMPUTERNAME"
    New-Item -ItemType Directory -Path $collectionPath -Force | Out-Null
    
    Write-IRLog "Output directory: $collectionPath" -Level Info
    
    # Check disk space
    if (-not (Test-DiskSpace -Path $collectionPath -RequiredGB 10)) {
        exit 1
    }
    
    $collectionMetadata = @{
        StartTime = Get-Date
        Modules   = @()
    }
    
    # Collection sequence (order by volatility)
    try {
        # 1. Memory (most volatile)
        if (-not $SkipMemory -and $script:Config.CollectMemory) {
            $memResult = Get-MemoryDump -OutputPath $collectionPath
            $collectionMetadata.Modules += @{Name = "Memory"; Result = $memResult }
        }
        
        # 2. Running processes and network
        if ($script:Config.CollectVolatileData) {
            Get-ProcessList -OutputPath $collectionPath
            Get-NetworkConnections -OutputPath $collectionPath
            $collectionMetadata.Modules += "Volatile Data"
        }
        
        # 3. Registry hives (using RawCopy or reg save)
        if ($script:Config.CollectRegistry) {
            Get-RegistryHives -OutputPath $collectionPath
            Get-UserRegistryHives -OutputPath $collectionPath
            $collectionMetadata.Modules += "Registry Hives"
        }
        
        # 4. File system artifacts (event logs, prefetch, user data, etc.)
        # Windows artifacts (event logs, prefetch, etc.)
        if ($script:Config.CollectWindowsArtifacts) {
            Get-WindowsArtifacts -OutputPath $collectionPath
            $collectionMetadata.Modules += "Windows Artifacts"
        }
        
        # User profile artifacts (NTUSER.DAT, browser data, recent files, etc.)
        if ($script:Config.CollectUserArtifacts) {
            Get-UserArtifacts -OutputPath $collectionPath
            $collectionMetadata.Modules += "User Artifacts"
        }
        
        # ProgramData artifacts (startup items, WER, Defender, 3rd party apps)
        if ($script:Config.CollectProgramData) {
            Get-ProgramDataArtifacts -OutputPath $collectionPath
            $collectionMetadata.Modules += "ProgramData Artifacts"
        }
        
        # NTFS artifacts (MFT and Journal)
        if ($script:Config.CollectNTFS) {
            Get-NTFSArtifacts -OutputPath $collectionPath
            $collectionMetadata.Modules += "NTFS Artifacts"
        }
        
        # Generate chain of custody
        $collectionMetadata.EndTime = Get-Date
        $collectionMetadata.Duration = ($collectionMetadata.EndTime - $collectionMetadata.StartTime).TotalMinutes
        
        New-ChainOfCustody -OutputPath $collectionPath -CollectionMetadata $collectionMetadata
        
        # Compress collection
        Compress-Collection -SourcePath $collectionPath
        
        Write-Host "`n=== Collection Complete ===" -ForegroundColor Green
        Write-Host "Total time: $([math]::Round($collectionMetadata.Duration, 2)) minutes"
        Write-Host "Output: $collectionPath"
        
    }
    catch {
        Write-IRLog "Collection failed: $_" -Level Error
        throw
    }
}

# Execute collection
Start-IRCollection