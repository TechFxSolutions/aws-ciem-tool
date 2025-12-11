# Cleanup Scripts

This directory contains cleanup scripts for the AWS CIEM Tool.

## ⚠️ IMPORTANT NOTICE

**The AWS CIEM Tool does NOT create any AWS resources.** It only reads and analyzes existing resources in your AWS account.

These scripts are provided for:
1. **Local cleanup** - Remove Docker containers and data
2. **Future use** - When auto-remediation or test environment features are added

---

## Scripts Overview

### 1. `cleanup.sh` - Local Resources Cleanup

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

### 2. `aws-cleanup.sh` - AWS Resources Cleanup (Future Use)

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

## Safety Features

### Local Cleanup Script (`cleanup.sh`)
- ✅ Confirmation prompt before deletion
- ✅ Option to keep scan data (`--keep-data`)
- ✅ Shows what will be removed before proceeding
- ✅ Provides summary of removed resources
- ✅ Safe to run multiple times

### AWS Cleanup Script (`aws-cleanup.sh`)
- ✅ Dry run mode to preview changes
- ✅ Requires typing "DELETE" to confirm
- ✅ Only deletes resources with specific tag
- ✅ Verifies AWS credentials before starting
- ✅ Shows detailed progress for each resource type
- ✅ Handles dependencies (detaches policies before deleting roles)

---

## When to Use Each Script

### Use `cleanup.sh` when:
- ✅ You want to completely remove the CIEM tool from your machine
- ✅ You want to free up disk space
- ✅ You want to start fresh with a clean installation
- ✅ You're done testing and want to clean up

### Use `aws-cleanup.sh` when:
- ⏳ **FUTURE**: When the tool adds resource creation features
- ⏳ **FUTURE**: When you've created test AWS resources with the project tag
- ⏳ **FUTURE**: When auto-remediation creates temporary resources
- ❌ **NOT NOW**: The tool doesn't create AWS resources yet

---

## Tagging Strategy (For Future Use)

When the tool starts creating AWS resources, they will be tagged with:

```json
{
  "Project": "AWS-CIEM-Tool",
  "ManagedBy": "CIEM-Tool",
  "Environment": "production|development|test",
  "CreatedBy": "auto-remediation|test-environment",
  "CreatedAt": "2025-12-11T10:30:00Z"
}
```

This allows:
- Easy identification of tool-created resources
- Automated cleanup
- Cost tracking
- Compliance auditing

---

## Troubleshooting

### Local Cleanup Issues

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

### AWS Cleanup Issues

**Problem**: "AWS CLI not found"
```bash
# Solution: Install AWS CLI
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
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

## Best Practices

### Before Running Cleanup

1. **Backup Important Data**
   ```bash
   # Export scan results
   docker exec ciem-postgres pg_dump -U ciem_user ciem_db > backup.sql
   
   # Export Neo4j data
   docker exec ciem-neo4j neo4j-admin dump --database=neo4j --to=/data/backup.dump
   ```

2. **Review What Will Be Deleted**
   ```bash
   # For local cleanup
   docker-compose ps
   docker volume ls | grep ciem
   
   # For AWS cleanup (dry run)
   ./scripts/aws-cleanup.sh --dry-run
   ```

3. **Test in Non-Production First**
   - Always test cleanup scripts in development environment
   - Verify backups before running in production

### After Running Cleanup

1. **Verify Cleanup**
   ```bash
   # Check Docker resources
   docker ps -a | grep ciem
   docker volume ls | grep ciem
   docker images | grep ciem
   
   # Check AWS resources (if applicable)
   aws ec2 describe-instances --filters "Name=tag:Project,Values=AWS-CIEM-Tool"
   ```

2. **Reinstall if Needed**
   ```bash
   # Reinstall CIEM tool
   docker-compose up -d
   ```

---

## FAQ

**Q: Will cleanup.sh delete my AWS resources?**  
A: No. It only removes local Docker containers and data. Your AWS resources are untouched.

**Q: Will aws-cleanup.sh delete all my AWS resources?**  
A: No. It only deletes resources tagged with `Project=AWS-CIEM-Tool`. Currently, the CIEM tool doesn't create any AWS resources, so this script won't find anything to delete.

**Q: Can I recover data after running cleanup.sh?**  
A: No, unless you backed up the Docker volumes first. Always backup important scan data before cleanup.

**Q: Is it safe to run cleanup scripts multiple times?**  
A: Yes. Both scripts are idempotent and safe to run multiple times.

**Q: Do I need AWS credentials to run cleanup.sh?**  
A: No. The local cleanup script doesn't interact with AWS at all.

**Q: Can I customize what gets deleted?**  
A: Yes. Both scripts are bash scripts you can modify. Read the code and adjust as needed.

---

## Support

If you encounter issues with cleanup scripts:

1. Check the troubleshooting section above
2. Review script output for error messages
3. Open an issue on GitHub with:
   - Script name
   - Command you ran
   - Error message
   - Your environment (OS, Docker version, AWS CLI version)

---

**Remember**: The CIEM tool is read-only. It doesn't create AWS resources, so the AWS cleanup script is for future use only.
