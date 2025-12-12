# Scan Failure Fix Guide

## 🔴 **Issue: Scans Failing Immediately**

If your scans are landing in "Failed" status, follow this diagnostic guide.

---

## 🔍 **Step 1: Check Backend Logs (MOST IMPORTANT)**

```bash
# View backend logs to see the actual error
docker-compose logs backend | tail -50

# Or follow logs in real-time
docker-compose logs -f backend
```

**Look for error messages like**:
- `NoCredentialsError`
- `InvalidAccessKeyId`
- `SignatureDoesNotMatch`
- `AccessDenied`
- `UnauthorizedOperation`
- `ClientError`
- `ConnectionError`

---

## 🔧 **Step 2: Verify AWS Credentials**

### **Check .env File**:

```bash
# View your AWS credentials
cat .env | grep AWS_

# Expected output:
# AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
# AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
# AWS_DEFAULT_REGION=us-east-1
```

### **Common Issues**:

❌ **Missing credentials**:
```bash
# .env shows:
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
```

✅ **Fix**:
```bash
nano .env

# Replace with ACTUAL credentials:
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=us-east-1

# Save and restart
docker-compose restart backend
```

❌ **Credentials with quotes**:
```bash
AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"  # ❌ Wrong
```

✅ **Fix**:
```bash
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE  # ✅ Correct (no quotes)
```

---

## 🧪 **Step 3: Test AWS Connection**

### **Test from Backend Container**:

```bash
# Enter backend container
docker-compose exec backend bash

# Test AWS CLI
aws sts get-caller-identity

# Expected output:
# {
#     "UserId": "AIDAI...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/your-user"
# }

# Exit container
exit
```

### **Test from API**:

```bash
# Test AWS connection endpoint
curl http://localhost:8000/api/v1/aws/test

# Expected response:
# {
#   "success": true,
#   "account_id": "123456789012",
#   "regions": ["us-east-1", ...],
#   "permissions": {
#     "iam": true,
#     "ec2": true,
#     "lambda": true
#   }
# }
```

**If this fails**, your AWS credentials are the problem.

---

## 🔐 **Step 4: Verify IAM Permissions**

Your AWS user needs **read-only** permissions. Check in AWS Console:

### **Required Permissions**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:GetUser",
        "iam:GetRole",
        "iam:GetPolicy",
        "iam:GetPolicyVersion",
        "iam:ListUsers",
        "iam:ListRoles",
        "iam:ListPolicies",
        "iam:ListAttachedUserPolicies",
        "iam:ListAttachedRolePolicies",
        "iam:ListUserPolicies",
        "iam:ListRolePolicies",
        "ec2:DescribeInstances",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeRegions",
        "lambda:GetFunction",
        "lambda:ListFunctions",
        "s3:GetBucketLocation",
        "s3:GetBucketPolicy",
        "s3:GetBucketAcl",
        "s3:ListAllMyBuckets",
        "rds:DescribeDBInstances",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

### **How to Apply**:

1. Go to **AWS Console** → **IAM** → **Users**
2. Select your user
3. Click **Add permissions** → **Attach policies directly**
4. Click **Create policy**
5. Switch to **JSON** tab
6. Paste the policy above
7. Name it: `CIEM-Tool-ReadOnly`
8. Click **Create policy**
9. Attach to your user

---

## 🐛 **Step 5: Common Error Solutions**

### **Error: "NoCredentialsError"**

**Cause**: AWS credentials not found

**Solution**:
```bash
# Check .env file exists
ls -la .env

# If missing, create it:
cp .env.example .env

# Edit with your credentials
nano .env

# Restart backend
docker-compose restart backend
```

---

### **Error: "InvalidAccessKeyId"**

**Cause**: Wrong access key or typo

**Solution**:
```bash
# Verify credentials in AWS Console
# IAM → Users → Your User → Security credentials

# Update .env with correct credentials
nano .env

# Restart backend
docker-compose restart backend
```

---

### **Error: "SignatureDoesNotMatch"**

**Cause**: Wrong secret key or special characters issue

**Solution**:
```bash
# Regenerate AWS credentials in AWS Console
# IAM → Users → Your User → Security credentials → Create access key

# Update .env with NEW credentials
nano .env

# Restart backend
docker-compose restart backend
```

---

### **Error: "AccessDenied" or "UnauthorizedOperation"**

**Cause**: IAM user lacks permissions

**Solution**:
1. Apply the IAM policy from Step 4
2. Wait 1-2 minutes for permissions to propagate
3. Test again:
   ```bash
   curl http://localhost:8000/api/v1/aws/test
   ```

---

### **Error: "An error occurred (RequestExpired)"**

**Cause**: System clock out of sync

**Solution**:
```bash
# Windows (PowerShell as Admin):
w32tm /resync

# macOS:
sudo sntp -sS time.apple.com

# Linux:
sudo ntpdate -s time.nist.gov

# Restart Docker
docker-compose restart
```

---

### **Error: "Unable to locate credentials"**

**Cause**: Environment variables not passed to container

**Solution**:
```bash
# Check docker-compose.yml has environment variables
cat docker-compose.yml | grep -A 10 "backend:" | grep AWS_

# Should show:
# - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
# - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
# - AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}

# Restart with fresh environment
docker-compose down
docker-compose up -d
```

---

## 🔄 **Step 6: Complete Reset and Retry**

If nothing works, do a complete reset:

```bash
# 1. Stop all containers
docker-compose down

# 2. Verify .env has correct credentials
cat .env | grep AWS_

# 3. If wrong, update:
nano .env

# 4. Start containers
docker-compose up -d

# 5. Wait for all services to be healthy
docker-compose ps

# 6. Test AWS connection
curl http://localhost:8000/api/v1/aws/test

# 7. Try scan again from UI
```

---

## 📊 **Step 7: Test with Minimal Scan**

Try a minimal scan to isolate the issue:

### **From UI**:
1. Go to http://localhost:3000/scan
2. Select **only one region**: `us-east-1`
3. Select **only IAM**: Uncheck all others
4. Click "Start Scan"

### **From API**:
```bash
curl -X POST http://localhost:8000/api/v1/scan/start \
  -H "Content-Type: application/json" \
  -d '{
    "regions": ["us-east-1"],
    "scan_iam": true,
    "scan_ec2": false,
    "scan_lambda": false,
    "scan_s3": false,
    "scan_rds": false,
    "scan_security_groups": false
  }'
```

**If this works**, gradually enable more services to find which one fails.

---

## 🔍 **Step 8: Detailed Error Diagnosis**

### **Get Scan Status with Error Details**:

```bash
# Get scan ID from UI or API response
SCAN_ID="your-scan-id-here"

# Get detailed status
curl http://localhost:8000/api/v1/scan/status/$SCAN_ID

# Response will include error message:
# {
#   "scan_id": "...",
#   "status": "failed",
#   "error": "Actual error message here",
#   "failed_at": "2025-12-12T01:00:00"
# }
```

### **Check Backend Logs for Specific Scan**:

```bash
# Replace SCAN_ID with your actual scan ID
docker-compose logs backend | grep "your-scan-id"
```

---

## 💡 **Step 9: Alternative - Use AWS Profile**

If environment variables don't work, use AWS profile:

### **Option A: Mount AWS Credentials**:

Edit `docker-compose.yml`:
```yaml
backend:
  volumes:
    - ./backend:/app
    - backend_logs:/app/logs
    - ~/.aws:/root/.aws:ro  # Add this line
```

Then:
```bash
docker-compose down
docker-compose up -d
```

### **Option B: Use IAM Role (EC2/ECS)**:

If running on EC2 or ECS, attach an IAM role instead of using credentials.

---

## 🎯 **Quick Diagnostic Checklist**

Run through this checklist:

- [ ] `.env` file exists
- [ ] AWS credentials in `.env` are actual values (not placeholders)
- [ ] No quotes around credential values
- [ ] Backend container is running: `docker-compose ps`
- [ ] Backend logs show no errors: `docker-compose logs backend`
- [ ] AWS test endpoint works: `curl http://localhost:8000/api/v1/aws/test`
- [ ] IAM user has required permissions
- [ ] System clock is synchronized
- [ ] Can run `aws sts get-caller-identity` from backend container

---

## 📞 **Still Failing? Get Detailed Logs**

```bash
# Get comprehensive diagnostic info
echo "=== Docker Status ==="
docker-compose ps

echo -e "\n=== Environment Variables ==="
cat .env | grep AWS_

echo -e "\n=== Backend Logs (last 100 lines) ==="
docker-compose logs backend | tail -100

echo -e "\n=== Test AWS Connection ==="
curl http://localhost:8000/api/v1/aws/test

echo -e "\n=== Test from Container ==="
docker-compose exec backend aws sts get-caller-identity
```

**Share this output** if you need further help.

---

## ✅ **Expected Successful Scan Flow**

When working correctly, you should see:

### **Backend Logs**:
```
INFO: Starting scan abc123-def456 for regions: ['us-east-1']
INFO: [abc123-def456] Discovering IAM resources
INFO: [abc123-def456] IAM discovery completed
INFO: [abc123-def456] Discovering resources in us-east-1
INFO: [abc123-def456] Resource discovery completed for us-east-1
INFO: [abc123-def456] Analyzing risks
INFO: [abc123-def456] Risk analysis completed
INFO: [abc123-def456] Building relationships
INFO: [abc123-def456] Relationship building completed
INFO: [abc123-def456] Scan completed successfully
```

### **UI**:
- Scan status: `queued` → `running` → `completed`
- Progress bar: 0% → 100%
- Risk summary updates with results

---

## 🚀 **Most Common Fix (90% of cases)**

```bash
# 1. Update .env with REAL credentials (no placeholders)
nano .env

# 2. Restart backend
docker-compose restart backend

# 3. Test connection
curl http://localhost:8000/api/v1/aws/test

# 4. Try scan again
```

---

**The scan failure is almost always due to AWS credentials or permissions. Follow this guide step by step to resolve it.**
