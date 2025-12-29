function New-ChainOfCustody {
    param(
        [string]$OutputPath,
        [hashtable]$CollectionMetadata
    )
    
    Write-IRLog "Generating chain of custody documentation..."
    
    $custody = @{
        CaseInformation = @{
            CollectionID = [guid]::NewGuid().ToString()
            Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            Collector = $env:USERNAME
            SystemName = $env:COMPUTERNAME
            SystemIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*"}).IPAddress
        }
        SystemInformation = @{
            OSVersion = (Get-CimInstance Win32_OperatingSystem).Caption
            OSBuild = (Get-CimInstance Win32_OperatingSystem).BuildNumber
            Architecture = $env:PROCESSOR_ARCHITECTURE
            TimeZone = (Get-TimeZone).Id
            LastBootTime = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
        }
        CollectionDetails = $CollectionMetadata
        FileIntegrity = @{}
    }
    
    # Hash all collected files
    Get-ChildItem -Path $OutputPath -Recurse -File | ForEach-Object {
        $hash = Get-FileHash -Path $_.FullName -Algorithm SHA256
        $relativePath = $_.FullName.Replace($OutputPath, "")
        $custody.FileIntegrity[$relativePath] = @{
            Hash = $hash.Hash
            Size = $_.Length
            Created = $_.CreationTime
            Modified = $_.LastWriteTime
        }
    }
    
    # Export custody document
    $custody | ConvertTo-Json -Depth 5 | Out-File (Join-Path $OutputPath "ChainOfCustody.json")
    
    # Create HTML report
    New-HTMLReport -CustodyData $custody -OutputPath $OutputPath
    
    Write-IRLog "Chain of custody documentation complete" -Level Success
}