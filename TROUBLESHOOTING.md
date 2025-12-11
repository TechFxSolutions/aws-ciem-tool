# Troubleshooting Guide

This guide helps resolve common issues when running the AWS CIEM Tool.

---

## 🔴 **Neo4j Container Issues**

### **Error: "dependency failed to start: container ciem-neo4j is unhealthy"**

This is the most common issue. Neo4j takes longer to start than other containers.

#### **Solution 1: Pull Latest Changes (RECOMMENDED)**

The docker-compose.yml has been updated with a better healthcheck:

```bash
# Stop all containers
docker-compose down

# Pull latest changes
git pull origin main

# Remove old Neo4j volume (optional, will delete scan data)
docker volume rm aws-ciem-tool_neo4j_data

# Start again
docker-compose up -d
```

#### **Solution 2: Check Neo4j Logs**

```bash
# View Neo4j logs
docker-compose logs neo4j

# Common issues in logs:
# - "Out of memory" → Increase Docker memory limit
# - "Permission denied" → Check volume permissions
# - "Plugin download failed" → Check internet connection
```

#### **Solution 3: Increase Docker Resources**

Neo4j needs adequate memory:

**Docker Desktop Settings**:
1. Open Docker Desktop
2. Go to Settings → Resources
3. Set Memory to at least **6 GB** (8 GB recommended)
4. Set CPUs to at least **2** (4 recommended)
5. Click "Apply & Restart"

Then restart containers:
```bash
docker-compose down
docker-compose up -d
```

#### **Solution 4: Wait Longer**

Neo4j can take 30-60 seconds to start:

```bash
# Watch Neo4j startup
docker-compose logs -f neo4j

# Wait for this message:
# "Started."
# "Remote interface available at http://localhost:7474/"

# Check health status
docker-compose ps

# When healthy, start backend
docker-compose up -d backend frontend
```

#### **Solution 5: Manual Neo4j Start**

Start services one by one:

```bash
# Stop everything
docker-compose down

# Start databases only
docker-compose up -d postgres neo4j redis

# Wait 60 seconds
sleep 60

# Check if Neo4j is healthy
docker-compose ps

# If healthy, start backend and frontend
docker-compose up -d backend frontend
```

#### **Solution 6: Simplified Neo4j Configuration**

If still failing, use minimal Neo4j config:

Edit `docker-compose.yml` Neo4j section:
```yaml
neo4j:
  image: neo4j:5-community
  container_name: ciem-neo4j
  environment:
    NEO4J_AUTH: neo4j/neo4j_password
  ports:
    - "7474:7474"
    - "7687:7687"
  volumes:
    - neo4j_data:/data
  networks:
    - ciem-network
  # Remove healthcheck temporarily
```

Then:
```bash
docker-compose down
docker-compose up -d
```

---

## 🔴 **Docker Issues**

### **Error: "Cannot connect to Docker daemon"**

**Windows**:
```powershell
# Start Docker Desktop from Start Menu
# Wait for Docker icon in system tray to show "Docker Desktop is running"
```

**Linux**:
```bash
# Start Docker service
sudo systemctl start docker

# Enable Docker on boot
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker
```

**macOS**:
```bash
# Start Docker Desktop from Applications
# Wait for Docker icon in menu bar
```

### **Error: "Port already in use"**

Check what's using the ports:

```bash
# Windows (PowerShell)
netstat -ano | findstr :8000
netstat -ano | findstr :3000
netstat -ano | findstr :7474

# macOS/Linux
lsof -i :8000
lsof -i :3000
lsof -i :7474
```

**Solution**: Stop the conflicting service or change ports in `docker-compose.yml`:

```yaml
backend:
  ports:
    - "8001:8000"  # Change 8000 to 8001

frontend:
  ports:
    - "3001:3000"  # Change 3000 to 3001
```

### **Error: "No space left on device"**

```bash
# Check Docker disk usage
docker system df

# Clean up unused resources
docker system prune -a --volumes

# WARNING: This removes all unused containers, images, and volumes
```

---

## 🔴 **Backend Issues**

### **Error: "Backend container keeps restarting"**

```bash
# Check backend logs
docker-compose logs backend

# Common issues:
# - Missing AWS credentials
# - Database connection failed
# - Python import errors
```

#### **Missing AWS Credentials**

```bash
# Check .env file exists
cat .env | grep AWS_ACCESS_KEY_ID

# If empty or missing, edit .env:
nano .env

# Add:
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_DEFAULT_REGION=us-east-1

# Restart backend
docker-compose restart backend
```

#### **Database Connection Failed**

```bash
# Check if databases are healthy
docker-compose ps

# All should show "Up (healthy)"
# If not, wait longer or check database logs:
docker-compose logs postgres
docker-compose logs neo4j
docker-compose logs redis
```

#### **Python Import Errors**

```bash
# Rebuild backend container
docker-compose build backend
docker-compose up -d backend
```

### **Error: "ModuleNotFoundError" in backend**

```bash
# Check if requirements.txt is complete
docker-compose exec backend pip list

# Rebuild with no cache
docker-compose build --no-cache backend
docker-compose up -d backend
```

---

## 🔴 **Frontend Issues**

### **Error: "Frontend shows blank page"**

```bash
# Check frontend logs
docker-compose logs frontend

# Check if backend is accessible
curl http://localhost:8000/health

# Check browser console (F12) for errors
```

#### **CORS Errors**

If you see CORS errors in browser console:

```bash
# Check REACT_APP_API_URL in .env
cat .env | grep REACT_APP_API_URL

# Should be:
REACT_APP_API_URL=http://localhost:8000

# Restart frontend
docker-compose restart frontend
```

#### **Module Not Found Errors**

```bash
# Rebuild frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### **Error: "Cannot connect to backend"**

```bash
# Test backend directly
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"AWS CIEM Tool","version":"0.1.0"}

# If backend not responding:
docker-compose logs backend
docker-compose restart backend
```

---

## 🔴 **AWS Connection Issues**

### **Error: "Invalid AWS credentials"**

```bash
# Test AWS credentials
aws sts get-caller-identity

# If error, reconfigure:
aws configure

# Or check .env file:
cat .env | grep AWS_
```

### **Error: "Access Denied" when scanning**

Your AWS user needs read permissions:

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

Apply this policy to your IAM user in AWS Console.

---

## 🔴 **Performance Issues**

### **Slow Scans**

```bash
# Increase Docker resources
# Docker Desktop → Settings → Resources
# - Memory: 8 GB or more
# - CPUs: 4 or more

# Check system resources
docker stats

# If containers using too much memory, restart:
docker-compose restart
```

### **High Memory Usage**

```bash
# Check memory usage
docker stats

# Reduce Neo4j memory in docker-compose.yml:
NEO4J_dbms_memory_heap_max__size: 1G  # Instead of 2G

# Restart
docker-compose down
docker-compose up -d
```

---

## 🔴 **Data Issues**

### **Lost Scan Data**

```bash
# Check if volumes exist
docker volume ls | grep ciem

# Restore from backup (if you made one):
docker run --rm -v aws-ciem-tool_postgres_data:/data -v $(pwd):/backup postgres:14-alpine tar xvf /backup/postgres-backup.tar -C /data
```

### **Corrupted Database**

```bash
# Stop containers
docker-compose down

# Remove volumes (WARNING: Deletes all scan data)
docker volume rm aws-ciem-tool_postgres_data
docker volume rm aws-ciem-tool_neo4j_data
docker volume rm aws-ciem-tool_redis_data

# Start fresh
docker-compose up -d
```

---

## 🔴 **Windows-Specific Issues**

### **WSL 2 Not Enabled**

```powershell
# Enable WSL 2
wsl --install

# Set WSL 2 as default
wsl --set-default-version 2

# Restart computer
```

### **Hyper-V Not Enabled**

```powershell
# Enable Hyper-V (requires restart)
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All

# Restart computer
Restart-Computer
```

### **Docker Desktop Won't Start**

1. Check BIOS virtualization is enabled (VT-x/AMD-V)
2. Update Windows to latest version
3. Reinstall Docker Desktop
4. Check Docker Desktop logs: `%LOCALAPPDATA%\Docker\log.txt`

---

## 🔴 **macOS-Specific Issues**

### **Rosetta Required (Apple Silicon)**

```bash
# Install Rosetta
softwareupdate --install-rosetta
```

### **Permission Denied**

```bash
# Fix Docker permissions
sudo chown -R $USER:staff ~/.docker
```

---

## 🔴 **Linux-Specific Issues**

### **Permission Denied**

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or:
newgrp docker
```

### **Docker Service Not Running**

```bash
# Start Docker
sudo systemctl start docker

# Enable on boot
sudo systemctl enable docker

# Check status
sudo systemctl status docker
```

---

## 🛠️ **Diagnostic Commands**

### **Check Everything**

```bash
# Container status
docker-compose ps

# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs neo4j

# Follow logs in real-time
docker-compose logs -f

# Check resource usage
docker stats

# Check volumes
docker volume ls

# Check networks
docker network ls

# Test backend health
curl http://localhost:8000/health

# Test Neo4j
curl http://localhost:7474

# Test frontend
curl http://localhost:3000
```

### **Complete Reset**

If nothing works, complete reset:

```bash
# Stop everything
docker-compose down -v

# Remove all project containers
docker rm -f $(docker ps -aq --filter name=ciem)

# Remove all project volumes
docker volume rm $(docker volume ls -q | grep ciem)

# Remove all project images
docker rmi $(docker images -q | grep ciem)

# Pull latest code
git pull origin main

# Start fresh
docker-compose up -d
```

---

## 📞 **Getting Help**

If issues persist:

1. **Check logs**: `docker-compose logs`
2. **Check GitHub Issues**: https://github.com/TechFxSolutions/aws-ciem-tool/issues
3. **Create new issue** with:
   - Error message
   - Output of `docker-compose logs`
   - Output of `docker-compose ps`
   - Your OS and Docker version
   - Steps to reproduce

---

## ✅ **Quick Fixes Summary**

| Issue | Quick Fix |
|-------|-----------|
| Neo4j unhealthy | `git pull && docker-compose down && docker-compose up -d` |
| Backend won't start | Check `.env` has AWS credentials |
| Frontend blank | Check `http://localhost:8000/health` works |
| Port in use | Change ports in `docker-compose.yml` |
| Out of memory | Increase Docker Desktop memory to 8GB |
| Slow startup | Wait 60 seconds, Neo4j takes time |
| Permission denied | Run as Administrator (Windows) or use `sudo` (Linux) |
| Can't connect to Docker | Start Docker Desktop |

---

**Most issues are resolved by pulling latest changes and restarting containers!**
