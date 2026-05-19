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
    
    Write-IRLog "Chain of custody documentation complete" -Level Success
}

function Compress-Collection {
    param([string]$SourcePath)
    
    Write-IRLog "Compressing collection..." -Level Info
    
    $archivePath = "$SourcePath.zip"
    
    try {
        # Load .NET compression assembly
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        
        # Use .NET ZipFile class which supports large files (Zip64)
        # CompressionLevel: Optimal = 1
        [System.IO.Compression.ZipFile]::CreateFromDirectory(
            $SourcePath, 
            $archivePath, 
            [System.IO.Compression.CompressionLevel]::Optimal, 
            $false
        )
        
        if (Test-Path $archivePath) {
            $archiveSize = [math]::Round((Get-Item $archivePath).Length / 1GB, 2)
            $archiveHash = Get-FileHash -Path $archivePath -Algorithm SHA256
            Write-IRLog "Archive created: $archivePath ($archiveSize GB)" -Level Success
            Write-IRLog "Archive hash (SHA256): $($archiveHash.Hash)" -Level Info
            
            return $archivePath
        }
    } catch {
        Write-IRLog "Failed to compress collection: $_" -Level Error
        Write-IRLog "Collection data is still available at: $SourcePath" -Level Warning
        return $null
    }
}

