#Requires -RunAsAdministrator

<#
.SYNOPSIS
    AWS CIEM Tool - Windows Prerequisites Installation Script

.DESCRIPTION
    This script automatically installs all required prerequisites for running
    the AWS CIEM Tool on Windows:
    - Chocolatey (package manager)
    - Docker Desktop
    - Git
    - AWS CLI (optional)
    - VS Code (optional)

.PARAMETER SkipOptional
    Skip installation of optional tools (AWS CLI, VS Code)

.PARAMETER SkipDocker
    Skip Docker Desktop installation (if already installed)

.PARAMETER SkipGit
    Skip Git installation (if already installed)

.EXAMPLE
    .\install-prerequisites-windows.ps1
    Install all prerequisites including optional tools

.EXAMPLE
    .\install-prerequisites-windows.ps1 -SkipOptional
    Install only required tools (Docker, Git)

.NOTES
    - Must be run as Administrator
    - Requires Windows 10/11 (64-bit)
    - Internet connection required
    - May require system restart
#>

param(
    [switch]$SkipOptional,
    [switch]$SkipDocker,
    [switch]$SkipGit
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green"
$WarningColor = "Yellow"
$InfoColor = "Cyan"

# Script configuration
$ChocolateyInstallUrl = "https://community.chocolatey.org/install.ps1"
$RequiresRestart = $false

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to check if running as Administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Function to check if a command exists
function Test-CommandExists {
    param([string]$Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# Function to check Windows version
function Test-WindowsVersion {
    $os = Get-CimInstance Win32_OperatingSystem
    $version = [System.Version]$os.Version
    
    # Windows 10 version 2004 (build 19041) or higher required for WSL 2
    if ($version.Build -lt 19041) {
        Write-ColorOutput "❌ Windows version too old. Windows 10 version 2004 (build 19041) or higher required." $ErrorColor
        Write-ColorOutput "   Current version: $($os.Caption) (build $($version.Build))" $WarningColor
        return $false
    }
    return $true
}

# Function to enable Windows features
function Enable-RequiredFeatures {
    Write-ColorOutput "`n[2/7] Checking Windows features..." $InfoColor
    
    $features = @(
        "Microsoft-Windows-Subsystem-Linux",
        "VirtualMachinePlatform"
    )
    
    $needsRestart = $false
    
    foreach ($feature in $features) {
        $featureState = Get-WindowsOptionalFeature -Online -FeatureName $feature -ErrorAction SilentlyContinue
        
        if ($null -eq $featureState) {
            Write-ColorOutput "⚠ Feature $feature not available on this system" $WarningColor
            continue
        }
        
        if ($featureState.State -ne "Enabled") {
            Write-ColorOutput "  Enabling $feature..." $InfoColor
            try {
                Enable-WindowsOptionalFeature -Online -FeatureName $feature -NoRestart -ErrorAction Stop | Out-Null
                Write-ColorOutput "  ✓ $feature enabled" $SuccessColor
                $needsRestart = $true
            }
            catch {
                Write-ColorOutput "  ⚠ Could not enable $feature. You may need to enable it manually." $WarningColor
            }
        }
        else {
            Write-ColorOutput "  ✓ $feature already enabled" $SuccessColor
        }
    }
    
    return $needsRestart
}

# Function to install Chocolatey
function Install-Chocolatey {
    Write-ColorOutput "`n[3/7] Installing Chocolatey package manager..." $InfoColor
    
    if (Test-CommandExists "choco") {
        Write-ColorOutput "  ✓ Chocolatey already installed" $SuccessColor
        return $true
    }
    
    try {
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString($ChocolateyInstallUrl))
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        if (Test-CommandExists "choco") {
            Write-ColorOutput "  ✓ Chocolatey installed successfully" $SuccessColor
            return $true
        }
        else {
            Write-ColorOutput "  ❌ Chocolatey installation failed" $ErrorColor
            return $false
        }
    }
    catch {
        Write-ColorOutput "  ❌ Error installing Chocolatey: $_" $ErrorColor
        return $false
    }
}

# Function to install Docker Desktop
function Install-DockerDesktop {
    if ($SkipDocker) {
        Write-ColorOutput "  ⊘ Skipping Docker Desktop installation" $WarningColor
        return $true
    }
    
    Write-ColorOutput "`n[4/7] Installing Docker Desktop..." $InfoColor
    
    if (Test-CommandExists "docker") {
        Write-ColorOutput "  ✓ Docker already installed" $SuccessColor
        docker --version
        return $true
    }
    
    try {
        choco install docker-desktop -y
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        Write-ColorOutput "  ✓ Docker Desktop installed" $SuccessColor
        Write-ColorOutput "  ⚠ You need to start Docker Desktop manually after installation" $WarningColor
        $script:RequiresRestart = $true
        return $true
    }
    catch {
        Write-ColorOutput "  ❌ Error installing Docker Desktop: $_" $ErrorColor
        Write-ColorOutput "  → Manual installation: https://www.docker.com/products/docker-desktop/" $InfoColor
        return $false
    }
}

# Function to install Git
function Install-Git {
    if ($SkipGit) {
        Write-ColorOutput "  ⊘ Skipping Git installation" $WarningColor
        return $true
    }
    
    Write-ColorOutput "`n[5/7] Installing Git..." $InfoColor
    
    if (Test-CommandExists "git") {
        Write-ColorOutput "  ✓ Git already installed" $SuccessColor
        git --version
        return $true
    }
    
    try {
        choco install git -y
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        if (Test-CommandExists "git") {
            Write-ColorOutput "  ✓ Git installed successfully" $SuccessColor
            git --version
            return $true
        }
        else {
            Write-ColorOutput "  ⚠ Git installed but not in PATH. Restart may be required." $WarningColor
            return $true
        }
    }
    catch {
        Write-ColorOutput "  ❌ Error installing Git: $_" $ErrorColor
        Write-ColorOutput "  → Manual installation: https://git-scm.com/download/win" $InfoColor
        return $false
    }
}

# Function to install AWS CLI
function Install-AWSCLI {
    if ($SkipOptional) {
        Write-ColorOutput "  ⊘ Skipping AWS CLI installation (optional)" $WarningColor
        return $true
    }
    
    Write-ColorOutput "`n[6/7] Installing AWS CLI (optional)..." $InfoColor
    
    if (Test-CommandExists "aws") {
        Write-ColorOutput "  ✓ AWS CLI already installed" $SuccessColor
        aws --version
        return $true
    }
    
    try {
        choco install awscli -y
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        if (Test-CommandExists "aws") {
            Write-ColorOutput "  ✓ AWS CLI installed successfully" $SuccessColor
            aws --version
            return $true
        }
        else {
            Write-ColorOutput "  ⚠ AWS CLI installed but not in PATH. Restart may be required." $WarningColor
            return $true
        }
    }
    catch {
        Write-ColorOutput "  ⚠ Error installing AWS CLI: $_" $WarningColor
        Write-ColorOutput "  → Manual installation: https://awscli.amazonaws.com/AWSCLIV2.msi" $InfoColor
        return $true  # Non-critical, return true
    }
}

# Function to install VS Code
function Install-VSCode {
    if ($SkipOptional) {
        Write-ColorOutput "  ⊘ Skipping VS Code installation (optional)" $WarningColor
        return $true
    }
    
    Write-ColorOutput "`n[7/7] Installing VS Code (optional)..." $InfoColor
    
    if (Test-CommandExists "code") {
        Write-ColorOutput "  ✓ VS Code already installed" $SuccessColor
        return $true
    }
    
    try {
        choco install vscode -y
        
        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        Write-ColorOutput "  ✓ VS Code installed successfully" $SuccessColor
        return $true
    }
    catch {
        Write-ColorOutput "  ⚠ Error installing VS Code: $_" $WarningColor
        Write-ColorOutput "  → Manual installation: https://code.visualstudio.com/download" $InfoColor
        return $true  # Non-critical, return true
    }
}

# Function to verify installations
function Test-Installations {
    Write-ColorOutput "`n╔════════════════════════════════════════════════════════════╗" $InfoColor
    Write-ColorOutput "║              Verifying Installations                       ║" $InfoColor
    Write-ColorOutput "╚════════════════════════════════════════════════════════════╝" $InfoColor
    
    $allGood = $true
    
    # Check Docker
    if (-not $SkipDocker) {
        Write-Host -NoNewline "  Docker Desktop: "
        if (Test-CommandExists "docker") {
            Write-ColorOutput "✓ Installed" $SuccessColor
            Write-ColorOutput "    Version: $(docker --version)" $InfoColor
        }
        else {
            Write-ColorOutput "✗ Not found" $ErrorColor
            $allGood = $false
        }
    }
    
    # Check Git
    if (-not $SkipGit) {
        Write-Host -NoNewline "  Git: "
        if (Test-CommandExists "git") {
            Write-ColorOutput "✓ Installed" $SuccessColor
            Write-ColorOutput "    Version: $(git --version)" $InfoColor
        }
        else {
            Write-ColorOutput "✗ Not found" $ErrorColor
            $allGood = $false
        }
    }
    
    # Check AWS CLI (optional)
    if (-not $SkipOptional) {
        Write-Host -NoNewline "  AWS CLI: "
        if (Test-CommandExists "aws") {
            Write-ColorOutput "✓ Installed" $SuccessColor
            Write-ColorOutput "    Version: $(aws --version)" $InfoColor
        }
        else {
            Write-ColorOutput "⚠ Not found (optional)" $WarningColor
        }
        
        Write-Host -NoNewline "  VS Code: "
        if (Test-CommandExists "code") {
            Write-ColorOutput "✓ Installed" $SuccessColor
        }
        else {
            Write-ColorOutput "⚠ Not found (optional)" $WarningColor
        }
    }
    
    return $allGood
}

# Main installation flow
function Start-Installation {
    Write-ColorOutput "╔════════════════════════════════════════════════════════════╗" $InfoColor
    Write-ColorOutput "║     AWS CIEM Tool - Windows Prerequisites Installer       ║" $InfoColor
    Write-ColorOutput "╚════════════════════════════════════════════════════════════╝" $InfoColor
    Write-ColorOutput ""
    
    # Check if running as Administrator
    Write-ColorOutput "[1/7] Checking administrator privileges..." $InfoColor
    if (-not (Test-Administrator)) {
        Write-ColorOutput "❌ This script must be run as Administrator!" $ErrorColor
        Write-ColorOutput "   Right-click PowerShell and select 'Run as Administrator'" $WarningColor
        exit 1
    }
    Write-ColorOutput "  ✓ Running as Administrator" $SuccessColor
    
    # Check Windows version
    if (-not (Test-WindowsVersion)) {
        Write-ColorOutput "`n❌ Installation cannot continue. Please update Windows." $ErrorColor
        exit 1
    }
    Write-ColorOutput "  ✓ Windows version compatible" $SuccessColor
    
    # Enable required Windows features
    $featuresNeedRestart = Enable-RequiredFeatures
    if ($featuresNeedRestart) {
        $script:RequiresRestart = $true
    }
    
    # Install Chocolatey
    if (-not (Install-Chocolatey)) {
        Write-ColorOutput "`n❌ Failed to install Chocolatey. Cannot continue." $ErrorColor
        exit 1
    }
    
    # Install Docker Desktop
    Install-DockerDesktop
    
    # Install Git
    Install-Git
    
    # Install AWS CLI (optional)
    Install-AWSCLI
    
    # Install VS Code (optional)
    Install-VSCode
    
    # Verify installations
    Write-ColorOutput ""
    $success = Test-Installations
    
    # Summary
    Write-ColorOutput "`n╔════════════════════════════════════════════════════════════╗" $SuccessColor
    Write-ColorOutput "║              Installation Complete!                        ║" $SuccessColor
    Write-ColorOutput "╚════════════════════════════════════════════════════════════╝" $SuccessColor
    Write-ColorOutput ""
    
    if ($RequiresRestart) {
        Write-ColorOutput "⚠ IMPORTANT: System restart required!" $WarningColor
        Write-ColorOutput "  Some features require a restart to work properly." $WarningColor
        Write-ColorOutput ""
        $restart = Read-Host "Do you want to restart now? (yes/no)"
        if ($restart -eq "yes" -or $restart -eq "y") {
            Write-ColorOutput "Restarting in 10 seconds..." $WarningColor
            Start-Sleep -Seconds 10
            Restart-Computer -Force
        }
        else {
            Write-ColorOutput "Please restart your computer manually before using the tools." $WarningColor
        }
    }
    else {
        Write-ColorOutput "✓ All prerequisites installed successfully!" $SuccessColor
    }
    
    Write-ColorOutput "`nNext steps:" $InfoColor
    Write-ColorOutput "  1. Start Docker Desktop from Start Menu" $InfoColor
    Write-ColorOutput "  2. Clone the repository:" $InfoColor
    Write-ColorOutput "     git clone https://github.com/TechFxSolutions/aws-ciem-tool.git" $InfoColor
    Write-ColorOutput "  3. Follow the setup instructions in QUICKSTART.md" $InfoColor
    Write-ColorOutput ""
}

# Run installation
try {
    Start-Installation
}
catch {
    Write-ColorOutput "`n❌ An unexpected error occurred: $_" $ErrorColor
    Write-ColorOutput "Stack trace: $($_.ScriptStackTrace)" $ErrorColor
    exit 1
}
