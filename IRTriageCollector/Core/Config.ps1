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