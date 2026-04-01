$script:Config = @{
    CollectionName          = "IR-Triage-Collection"
    OutputPath              = "$PSScriptRoot\..\Output"
    LogPath                 = "$PSScriptRoot\..\Logs"
    ToolsPath               = "$PSScriptRoot\..\Tools"
    
    # Collection toggles - Enable/disable specific artifact collection
    CollectMemory           = $false
    CollectRegistry         = $true
    CollectVolatileData     = $true  # Process list and network connections
    CollectEventLogs        = $true
    CollectPrefetch         = $false
    CollectWindowsArtifacts = $true  # Event logs, prefetch, AppCompat, etc.
    CollectUserArtifacts    = $true  # Browser data, recent files, PowerShell history, etc.
    CollectProgramData      = $true  # Startup items, WER, Defender, 3rd party apps
    CollectNTFS             = $true  # MFT and USN Journal
    Compress                = $true # Whether to compress the collection output into a ZIP file - Should be enabled
                                    # because Ansible can only transfer zip file, not folder.
    
    # Hash algorithm
    HashAlgorithm           = "SHA256"
}