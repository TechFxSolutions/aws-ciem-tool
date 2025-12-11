# Scripts Directory

This directory contains utility scripts for the AWS CIEM Tool.

## ⚠️ IMPORTANT NOTICE

**The AWS CIEM Tool does NOT create any AWS resources.** It only reads and analyzes existing resources in your AWS account.

---

## 📋 **Scripts Overview**

### 1. `install-prerequisites-windows.ps1` - Windows Prerequisites Installer

**Purpose**: Automatically install all required tools on Windows.

**What it installs**:
- ✅ Chocolatey (package manager)
- ✅ Docker Desktop
- ✅ Git
- ✅ AWS CLI (optional)
- ✅ VS Code (optional)
- ✅ Enables WSL 2 and required Windows features

**Requirements**:
- Windows 10/11 (64-bit)
- Administrator privileges
- Internet connection

**Usage**:
```powershell
# Open PowerShell as Administrator
# Navigate to project directory
cd aws-ciem-tool

# Install all prerequisites (including optional tools)
.\scripts\install-prerequisites-windows.ps1

# Install only required tools (skip AWS CLI and VS Code)
.\scripts\install-prerequisites-windows.ps1 -SkipOptional

# Skip Docker installation (if already installed)
.\scripts\install-prerequisites-windows.ps1 -SkipDocker

# Skip Git installation (if already installed)
.\scripts\install-prerequisites-windows.ps1 -SkipGit
```

**Example Output**:
```
╔════════════════════════════════════════════════════════════╗
║     AWS CIEM Tool - Windows Prerequisites Installer       ║
╚════════════════════════════════════════════════════════════╝

[1/7] Checking administrator privileges...
  ✓ Running as Administrator
  ✓ Windows version compatible

[2/7] Checking Windows features...
  ✓ Microsoft-Windows-Subsystem-Linux already enabled
  ✓ VirtualMachinePlatform already enabled

[3/7] Installing Chocolatey package manager...
  ✓ Chocolatey installed successfully

[4/7] Installing Docker Desktop...
  ✓ Docker Desktop installed

[5/7] Installing Git...
  ✓ Git installed successfully

[6/7] Installing AWS CLI (optional)...
  ✓ AWS CLI installed successfully

[7/7] Installing VS Code (optional)...
  ✓ VS Code installed successfully

╔════════════════════════════════════════════════════════════╗
║              Installation Complete!                        ║
╚════════════════════════════════════════════════════════════╝
```

---

### 2. `cleanup.sh` - Local Resources Cleanup

**Purpose**: Remove all local Docker resources created by the CIEM tool.

**What it removes**:
- ✅ Docker containers (backend, frontend, postgres, neo4j, redis)
- ✅ Docker volumes (scan data)
- ✅ Docker images
- ✅ Docker networks
- ✅ Log files
- ✅ node_modules (optional)

**What it does NOT remove**:
- ❌ AWS resources (the tool doesn't create any)
- ❌ Source code
- ❌ Configuration files

**Usage**:
```bash
# Make script executable
chmod +x scripts/cleanup.sh

# Run cleanup (removes everything including scan data)
./scripts/cleanup.sh

# Run cleanup but keep scan data
./scripts/cleanup.sh --keep-data
```

**Example Output**:
```
╔════════════════════════════════════════════════════════════╗
║         AWS CIEM Tool - Cleanup Script                     ║
╚════════════════════════════════════════════════════════════╝

This will remove:
  - All Docker containers
  - All Docker networks
  - All Docker images for this project
  - All Docker volumes (scan data will be DELETED)
  - Log files

WARNING: This action cannot be undone!

Are you sure you want to continue? (yes/no): yes

Starting cleanup...
[1/6] Stopping Docker containers...
✓ Containers stopped
...
```

---

### 3. `aws-cleanup.sh` - AWS Resources Cleanup (Future Use)

**Purpose**: Delete AWS resources tagged with `Project=AWS-CIEM-Tool`.

**⚠️ IMPORTANT**: This script is for **FUTURE USE** when the tool creates AWS resources. Currently, the CIEM tool only reads existing resources.

**What it searches for and deletes**:
- EC2 instances
- S3 buckets
- RDS instances
- Lambda functions
- Security Groups
- IAM Roles
- IAM Users
- IAM Policies

**All resources must be tagged with**:
- Tag Key: `Project`
- Tag Value: `AWS-CIEM-Tool`

**Usage**:
```bash
# Make script executable
chmod +x scripts/aws-cleanup.sh

# Dry run (see what would be deleted without actually deleting)
./scripts/aws-cleanup.sh --region us-east-1 --profile default --dry-run

# Actually delete resources (requires typing "DELETE" to confirm)
./scripts/aws-cleanup.sh --region us-east-1 --profile default

# Use different region
./scripts/aws-cleanup.sh --region eu-west-1 --profile production
```

**Example Output**:
```
╔════════════════════════════════════════════════════════════╗
║     AWS CIEM Tool - AWS Resources Cleanup Script          ║
╚════════════════════════════════════════════════════════════╝

Configuration:
  Region: us-east-1
  Profile: default
  Tag Key: Project
  Tag Value: AWS-CIEM-Tool
  Mode: DRY RUN (no resources will be deleted)

Verifying AWS credentials...
✓ Connected to AWS Account: 123456789012

Starting AWS resource discovery...

[1/8] Searching for EC2 instances...
✓ No EC2 instances found

[2/8] Searching for S3 buckets...
✓ No S3 buckets found
...
```

---

## 🚀 **Quick Start Workflow**

### **For Windows Users**:

1. **Install Prerequisites**
   ```powershell
   # Run as Administrator
   .\scripts\install-prerequisites-windows.ps1
   ```

2. **Restart Computer** (if prompted)

3. **Start Docker Desktop** (from Start Menu)

4. **Clone Repository** (if not already done)
   ```powershell
   git clone https://github.com/TechFxSolutions/aws-ciem-tool.git
   cd aws-ciem-tool
   ```

5. **Configure Environment**
   ```powershell
   cp .env.example .env
   # Edit .env with your AWS credentials
   ```

6. **Start Application**
   ```powershell
   docker-compose up -d
   ```

### **For macOS/Linux Users**:

1. **Install Prerequisites** (see `PREREQUISITES.md`)

2. **Clone Repository**
   ```bash
   git clone https://github.com/TechFxSolutions/aws-ciem-tool.git
   cd aws-ciem-tool
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials
   ```

4. **Start Application**
   ```bash
   docker-compose up -d
   ```

---

## 🛡️ **Safety Features**

### **Installation Script** (`install-prerequisites-windows.ps1`)
- ✅ Requires Administrator privileges
- ✅ Checks Windows version compatibility
- ✅ Verifies each installation
- ✅ Provides detailed progress output
- ✅ Handles errors gracefully
- ✅ Optional tools can be skipped
- ✅ Prompts for restart if needed

### **Local Cleanup Script** (`cleanup.sh`)
- ✅ Confirmation prompt before deletion
- ✅ Option to keep scan data (`--keep-data`)
- ✅ Shows what will be removed before proceeding
- ✅ Provides summary of removed resources
- ✅ Safe to run multiple times

### **AWS Cleanup Script** (`aws-cleanup.sh`)
- ✅ Dry run mode to preview changes
- ✅ Requires typing "DELETE" to confirm
- ✅ Only deletes resources with specific tag
- ✅ Verifies AWS credentials before starting
- ✅ Shows detailed progress for each resource type
- ✅ Handles dependencies (detaches policies before deleting roles)

---

## 📊 **When to Use Each Script**

### **Use `install-prerequisites-windows.ps1` when**:
- ✅ Setting up a new Windows machine
- ✅ You don't have Docker or Git installed
- ✅ You want automated installation
- ✅ You're new to development tools

### **Use `cleanup.sh` when**:
- ✅ You want to completely remove the CIEM tool from your machine
- ✅ You want to free up disk space
- ✅ You want to start fresh with a clean installation
- ✅ You're done testing and want to clean up

### **Use `aws-cleanup.sh` when**:
- ⏳ **FUTURE**: When the tool adds resource creation features
- ⏳ **FUTURE**: When you've created test AWS resources with the project tag
- ⏳ **FUTURE**: When auto-remediation creates temporary resources
- ❌ **NOT NOW**: The tool doesn't create AWS resources yet

---

## 🐛 **Troubleshooting**

### **Windows Installation Issues**

**Problem**: "Script execution is disabled"
```powershell
# Solution: Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Problem**: "Not running as Administrator"
```powershell
# Solution: Right-click PowerShell and select "Run as Administrator"
```

**Problem**: Chocolatey installation fails
```powershell
# Solution: Install manually
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

**Problem**: Docker Desktop won't start
- Enable Hyper-V and WSL 2 in Windows Features
- Update Windows to latest version
- Check BIOS virtualization settings (VT-x/AMD-V must be enabled)

### **Local Cleanup Issues**

**Problem**: "Permission denied" error
```bash
# Solution: Make script executable
chmod +x scripts/cleanup.sh
```

**Problem**: Containers won't stop
```bash
# Solution: Force stop
docker-compose down --remove-orphans
docker stop $(docker ps -aq --filter name=ciem)
```

**Problem**: Volumes won't delete
```bash
# Solution: Force remove
docker volume rm $(docker volume ls -q | grep ciem) --force
```

### **AWS Cleanup Issues**

**Problem**: "AWS CLI not found"
```bash
# Solution: Install AWS CLI
# Windows: choco install awscli
# macOS: brew install awscli
# Linux: See PREREQUISITES.md
```

**Problem**: "Invalid credentials"
```bash
# Solution: Configure AWS CLI
aws configure --profile default
```

**Problem**: "Access denied" errors
```bash
# Solution: Ensure your IAM user has delete permissions
# The user needs policies like:
# - AmazonEC2FullAccess
# - AmazonS3FullAccess
# - IAMFullAccess
# etc.
```

---

## 📚 **Additional Resources**

- **Prerequisites Guide**: See `PREREQUISITES.md` for detailed requirements
- **Quick Start Guide**: See `QUICKSTART.md` for usage instructions
- **Architecture**: See `docs/ARCHITECTURE.md` for system design
- **AWS Setup**: See `docs/AWS_SETUP.md` for AWS configuration

---

## ❓ **FAQ**

**Q: Do I need to run the installation script if I already have Docker?**  
A: No, you can skip Docker installation with `-SkipDocker` flag.

**Q: Will the installation script modify my existing tools?**  
A: No, it checks if tools are already installed and skips them.

**Q: Can I run the installation script multiple times?**  
A: Yes, it's safe to run multiple times. It will skip already installed tools.

**Q: Do I need to restart after installation?**  
A: Usually yes, especially if Windows features were enabled or Docker was installed.

**Q: Will cleanup.sh delete my AWS resources?**  
A: No. It only removes local Docker containers and data. Your AWS resources are untouched.

**Q: Will aws-cleanup.sh delete all my AWS resources?**  
A: No. It only deletes resources tagged with `Project=AWS-CIEM-Tool`. Currently, the CIEM tool doesn't create any AWS resources.

**Q: Can I recover data after running cleanup.sh?**  
A: No, unless you backed up the Docker volumes first. Always backup important scan data before cleanup.

**Q: Is it safe to run cleanup scripts multiple times?**  
A: Yes. Both scripts are idempotent and safe to run multiple times.

---

**For more help, see `PREREQUISITES.md` or open an issue on GitHub.**
