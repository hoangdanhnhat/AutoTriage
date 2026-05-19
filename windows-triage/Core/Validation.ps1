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