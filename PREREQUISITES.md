# Prerequisites for AWS CIEM Tool

This document lists all the tools and dependencies required to run the AWS CIEM Tool on different operating systems.

---

## 📋 **Required Tools**

### **1. Docker Desktop**
- **Purpose**: Run containerized services (PostgreSQL, Neo4j, Redis, Backend, Frontend)
- **Minimum Version**: 20.10.0 or higher
- **Required For**: All deployment methods

### **2. Docker Compose**
- **Purpose**: Orchestrate multiple Docker containers
- **Minimum Version**: 2.0.0 or higher
- **Note**: Included with Docker Desktop

### **3. Git**
- **Purpose**: Clone the repository
- **Minimum Version**: 2.30.0 or higher
- **Required For**: Getting the source code

### **4. AWS CLI (Optional but Recommended)**
- **Purpose**: Test AWS credentials and permissions
- **Minimum Version**: 2.0.0 or higher
- **Required For**: Verifying AWS setup

### **5. Text Editor**
- **Purpose**: Edit configuration files (.env)
- **Options**: VS Code, Notepad++, Sublime Text, Vim, Nano
- **Recommended**: VS Code

---

## 💻 **System Requirements**

### **Minimum Requirements**
- **OS**: Windows 10/11 (64-bit), macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM**: 8 GB
- **Disk Space**: 10 GB free
- **CPU**: 2 cores
- **Internet**: Required for Docker images and AWS API calls

### **Recommended Requirements**
- **RAM**: 16 GB or more
- **Disk Space**: 20 GB free
- **CPU**: 4 cores or more
- **SSD**: For better performance

---

## 🪟 **Windows Installation**

### **Automated Installation (Recommended)**

We provide a PowerShell script that installs all prerequisites automatically.

```powershell
# Run PowerShell as Administrator
# Navigate to project directory
cd aws-ciem-tool

# Run installation script
.\scripts\install-prerequisites-windows.ps1
```

### **Manual Installation**

#### **1. Install Docker Desktop**
1. Download from: https://www.docker.com/products/docker-desktop/
2. Run the installer
3. Follow installation wizard
4. Restart computer when prompted
5. Launch Docker Desktop
6. Verify installation:
   ```powershell
   docker --version
   docker-compose --version
   ```

#### **2. Install Git**
1. Download from: https://git-scm.com/download/win
2. Run the installer
3. Use default settings (recommended)
4. Verify installation:
   ```powershell
   git --version
   ```

#### **3. Install AWS CLI (Optional)**
1. Download from: https://awscli.amazonaws.com/AWSCLIV2.msi
2. Run the installer
3. Follow installation wizard
4. Verify installation:
   ```powershell
   aws --version
   ```

#### **4. Install Text Editor (Optional)**
- **VS Code**: https://code.visualstudio.com/download
- **Notepad++**: https://notepad-plus-plus.org/downloads/

---

## 🍎 **macOS Installation**

### **Using Homebrew (Recommended)**

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Docker Desktop
brew install --cask docker

# Install Git
brew install git

# Install AWS CLI (optional)
brew install awscli

# Install VS Code (optional)
brew install --cask visual-studio-code
```

### **Manual Installation**

1. **Docker Desktop**: https://www.docker.com/products/docker-desktop/
2. **Git**: https://git-scm.com/download/mac
3. **AWS CLI**: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

---

## 🐧 **Linux Installation**

### **Ubuntu/Debian**

```bash
# Update package list
sudo apt update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Install Git
sudo apt install git

# Install AWS CLI (optional)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Restart to apply Docker group changes
sudo reboot
```

### **CentOS/RHEL/Fedora**

```bash
# Install Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install Git
sudo yum install git

# Install AWS CLI (optional)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Restart to apply Docker group changes
sudo reboot
```

---

## ✅ **Verification Steps**

After installation, verify all tools are working:

### **Windows (PowerShell)**
```powershell
# Check Docker
docker --version
docker-compose --version
docker ps

# Check Git
git --version

# Check AWS CLI (if installed)
aws --version

# Test Docker
docker run hello-world
```

### **macOS/Linux (Terminal)**
```bash
# Check Docker
docker --version
docker-compose --version
docker ps

# Check Git
git --version

# Check AWS CLI (if installed)
aws --version

# Test Docker
docker run hello-world
```

**Expected Output**:
- Docker version 20.10.0 or higher
- Docker Compose version 2.0.0 or higher
- Git version 2.30.0 or higher
- AWS CLI version 2.0.0 or higher (if installed)
- "Hello from Docker!" message from test container

---

## 🔧 **AWS Configuration**

After installing AWS CLI, configure your credentials:

```bash
# Configure AWS credentials
aws configure

# You'll be prompted for:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
# - Default output format (json recommended)
```

**Test AWS connection**:
```bash
aws sts get-caller-identity
```

---

## 🐛 **Troubleshooting**

### **Windows Issues**

#### **Docker Desktop won't start**
- Enable Hyper-V and WSL 2 in Windows Features
- Update Windows to latest version
- Check BIOS virtualization settings (VT-x/AMD-V must be enabled)

#### **"Docker daemon not running" error**
- Start Docker Desktop application
- Wait for Docker to fully start (whale icon in system tray)
- Check Docker Desktop settings

#### **Permission denied errors**
- Run PowerShell as Administrator
- Add your user to "docker-users" group in Windows

### **macOS Issues**

#### **Docker Desktop requires Rosetta on Apple Silicon**
```bash
softwareupdate --install-rosetta
```

#### **Permission denied when running Docker**
```bash
sudo chown -R $USER:staff ~/.docker
```

### **Linux Issues**

#### **Permission denied when running Docker**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Restart or log out and back in
sudo reboot
```

#### **Docker service not starting**
```bash
# Check Docker status
sudo systemctl status docker

# Start Docker
sudo systemctl start docker

# Enable Docker on boot
sudo systemctl enable docker
```

---

## 📦 **Optional Tools**

### **For Development**

- **Node.js** (v16+): For frontend development without Docker
- **Python** (v3.9+): For backend development without Docker
- **PostgreSQL Client**: For database inspection
- **Neo4j Desktop**: For graph database visualization
- **Postman/Insomnia**: For API testing

### **For Monitoring**

- **Docker Desktop Dashboard**: Built-in container monitoring
- **Portainer**: Web-based Docker management UI
- **Lazydocker**: Terminal-based Docker management

---

## 🔐 **AWS IAM Permissions**

The AWS user/role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:Get*",
        "iam:List*",
        "ec2:Describe*",
        "lambda:Get*",
        "lambda:List*",
        "s3:GetBucket*",
        "s3:ListAllMyBuckets",
        "rds:Describe*",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

**Note**: All permissions are read-only. The tool does not modify AWS resources.

---

## 📊 **Disk Space Breakdown**

Approximate disk space usage:

- **Docker Images**: ~3 GB
  - PostgreSQL: ~300 MB
  - Neo4j: ~600 MB
  - Redis: ~100 MB
  - Backend: ~1 GB
  - Frontend: ~1 GB

- **Docker Volumes**: ~1-5 GB (depends on scan data)
  - PostgreSQL data: ~500 MB - 2 GB
  - Neo4j data: ~500 MB - 2 GB
  - Redis data: ~100 MB - 500 MB

- **Source Code**: ~50 MB

**Total**: ~5-10 GB

---

## 🚀 **Next Steps**

After installing prerequisites:

1. **Clone Repository**
   ```bash
   git clone https://github.com/TechFxSolutions/aws-ciem-tool.git
   cd aws-ciem-tool
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials
   ```

3. **Start Application**
   ```bash
   docker-compose up -d
   ```

4. **Access Dashboard**
   - Open http://localhost:3000

---

## 📚 **Additional Resources**

- **Docker Documentation**: https://docs.docker.com/
- **Git Documentation**: https://git-scm.com/doc
- **AWS CLI Documentation**: https://docs.aws.amazon.com/cli/
- **Project Quick Start**: See `QUICKSTART.md`
- **Project Documentation**: See `docs/` directory

---

## ❓ **FAQ**

**Q: Do I need to install Python or Node.js?**  
A: No, if using Docker. All dependencies are included in containers.

**Q: Can I run this without Docker?**  
A: Yes, but you'll need to manually install PostgreSQL, Neo4j, Redis, Python 3.9+, and Node.js 16+. Docker is strongly recommended.

**Q: How much RAM does this need?**  
A: Minimum 8 GB, but 16 GB recommended for better performance.

**Q: Do I need AWS credentials to install?**  
A: No, but you need them to run scans. Installation can be done without AWS credentials.

**Q: Can I use this on Windows Home edition?**  
A: Yes, but you need Windows 10/11 Home version 2004 or higher with WSL 2 support.

**Q: Is internet connection required?**  
A: Yes, for downloading Docker images and making AWS API calls. After initial setup, only AWS API calls require internet.

---

**For installation issues, see the Troubleshooting section or open an issue on GitHub.**
