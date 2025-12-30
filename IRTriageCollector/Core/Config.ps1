$script:Config = @{
    CollectionName          = "IR-Triage-Collection"
    OutputPath              = "$PSScriptRoot\..\Output"
    LogPath                 = "$PSScriptRoot\..\Logs"
    ToolsPath               = "$PSScriptRoot\..\Tools"
    
    # Collection toggles - Enable/disable specific artifact collection
    CollectMemory           = $true
    CollectRegistry         = $true
    CollectVolatileData     = $true      # Process list and network connections
    CollectEventLogs        = $true
    CollectPrefetch         = $true
    CollectWindowsArtifacts = $true  # Event logs, prefetch, AppCompat, etc.
    CollectUserArtifacts    = $true     # Browser data, recent files, PowerShell history, etc.
    CollectProgramData      = $true       # Startup items, WER, Defender, 3rd party apps
    CollectNTFS             = $true              # MFT and USN Journal
    
    # Event log settings
    EventLogsToCollect      = @(
        "Security", "System", "Application",
        "Microsoft-Windows-Sysmon/Operational",
        "Microsoft-Windows-PowerShell/Operational"
    )
    
    # Hash algorithm
    HashAlgorithm           = "SHA256"
}