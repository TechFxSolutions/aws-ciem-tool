# AWS Setup Guide

Complete guide for setting up AWS credentials and permissions for the CIEM Tool.

## Prerequisites

- AWS Account with administrative access
- AWS CLI installed (optional but recommended)

## Option 1: IAM User with Access Keys (Recommended for Development)

### Step 1: Create IAM User

1. Log in to AWS Console
2. Navigate to **IAM** → **Users** → **Create user**
3. User name: `ciem-tool-scanner`
4. Select **Programmatic access**
5. Click **Next**

### Step 2: Attach Permissions

Create a custom policy with read-only permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CIEMToolReadOnlyAccess",
      "Effect": "Allow",
      "Action": [
        "iam:Get*",
        "iam:List*",
        "iam:GenerateCredentialReport",
        "iam:GenerateServiceLastAccessedDetails",
        "ec2:Describe*",
        "ec2:Get*",
        "lambda:Get*",
        "lambda:List*",
        "s3:GetBucket*",
        "s3:GetObject*",
        "s3:ListAllMyBuckets",
        "s3:ListBucket",
        "s3:GetAccountPublicAccessBlock",
        "rds:Describe*",
        "rds:ListTagsForResource",
        "cloudtrail:LookupEvents",
        "cloudtrail:GetTrailStatus",
        "cloudtrail:DescribeTrails",
        "cloudwatch:Describe*",
        "cloudwatch:Get*",
        "cloudwatch:List*",
        "logs:Describe*",
        "logs:Get*",
        "logs:FilterLogEvents",
        "sts:GetCallerIdentity",
        "organizations:Describe*",
        "organizations:List*",
        "access-analyzer:List*",
        "access-analyzer:Get*"
      ],
      "Resource": "*"
    }
  ]
}
```

**To create the policy:**

1. Go to **IAM** → **Policies** → **Create policy**
2. Click **JSON** tab
3. Paste the policy above
4. Name it: `CIEMToolReadOnlyPolicy`
5. Click **Create policy**

**Attach to user:**

1. Go back to user creation
2. Click **Attach policies directly**
3. Search for `CIEMToolReadOnlyPolicy`
4. Select it and click **Next**
5. Click **Create user**

### Step 3: Generate Access Keys

1. Click on the created user
2. Go to **Security credentials** tab
3. Click **Create access key**
4. Select **Application running outside AWS**
5. Click **Next** → **Create access key**
6. **IMPORTANT**: Download the CSV or copy the keys immediately
   - Access Key ID: `AKIA...`
   - Secret Access Key: `wJalrXUtn...`

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=wJalrXUtn...
AWS_DEFAULT_REGION=us-east-1

# Optional: Multiple regions
AWS_REGIONS=us-east-1,us-west-2,eu-west-1
```

---

## Option 2: AWS CLI Profile (Recommended for Local Development)

### Step 1: Install AWS CLI

```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Windows
# Download from: https://awscli.amazonaws.com/AWSCLIV2.msi
```

### Step 2: Configure AWS CLI

```bash
aws configure --profile ciem-tool

# Enter when prompted:
AWS Access Key ID: AKIA...
AWS Secret Access Key: wJalrXUtn...
Default region name: us-east-1
Default output format: json
```

### Step 3: Verify Configuration

```bash
aws sts get-caller-identity --profile ciem-tool
```

Expected output:
```json
{
    "UserId": "AIDAI...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/ciem-tool-scanner"
}
```

### Step 4: Use Profile in Application

Set environment variable:

```bash
export AWS_PROFILE=ciem-tool
```

Or in `.env`:
```bash
AWS_PROFILE=ciem-tool
```

---

## Option 3: IAM Role (Recommended for Production)

### For EC2 Instances

#### Step 1: Create IAM Role

1. Go to **IAM** → **Roles** → **Create role**
2. Select **AWS service** → **EC2**
3. Click **Next**

#### Step 2: Attach Policy

1. Search for `CIEMToolReadOnlyPolicy` (created earlier)
2. Select it and click **Next**
3. Role name: `CIEMToolEC2Role`
4. Click **Create role**

#### Step 3: Attach Role to EC2

1. Go to **EC2** → **Instances**
2. Select your instance
3. **Actions** → **Security** → **Modify IAM role**
4. Select `CIEMToolEC2Role`
5. Click **Update IAM role**

#### Step 4: No Credentials Needed

The application will automatically use the instance role. No need to set `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY`.

### For ECS/Fargate

Add to task definition:

```json
{
  "taskRoleArn": "arn:aws:iam::123456789012:role/CIEMToolEC2Role",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole"
}
```

### For Lambda

Set execution role in Lambda configuration:

```bash
aws lambda update-function-configuration \
  --function-name ciem-tool \
  --role arn:aws:iam::123456789012:role/CIEMToolEC2Role
```

---

## Option 4: AWS SSO (Recommended for Organizations)

### Step 1: Configure SSO

```bash
aws configure sso

# Follow prompts:
SSO start URL: https://my-sso-portal.awsapps.com/start
SSO Region: us-east-1
```

### Step 2: Login

```bash
aws sso login --profile ciem-tool-sso
```

### Step 3: Use SSO Profile

```bash
export AWS_PROFILE=ciem-tool-sso
```

---

## Multi-Account Setup

For scanning multiple AWS accounts:

### Step 1: Create Cross-Account Role

In each target account, create a role with trust relationship:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::MAIN_ACCOUNT_ID:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "ciem-tool-external-id"
        }
      }
    }
  ]
}
```

### Step 2: Configure in Application

Add to `.env`:

```bash
# Main account credentials
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=wJalrXUtn...

# Cross-account roles
CROSS_ACCOUNT_ROLES=arn:aws:iam::111111111111:role/CIEMToolRole,arn:aws:iam::222222222222:role/CIEMToolRole
EXTERNAL_ID=ciem-tool-external-id
```

---

## Least Privilege Policy (Minimal Permissions)

For maximum security, use this minimal policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:ListUsers",
        "iam:ListRoles",
        "iam:ListGroups",
        "iam:ListPolicies",
        "iam:GetUser",
        "iam:GetRole",
        "iam:GetGroup",
        "iam:GetPolicy",
        "iam:ListAttachedUserPolicies",
        "iam:ListAttachedRolePolicies",
        "iam:ListAttachedGroupPolicies",
        "iam:ListUserPolicies",
        "iam:ListRolePolicies",
        "iam:ListGroupPolicies",
        "iam:ListMFADevices",
        "iam:ListAccessKeys",
        "ec2:DescribeInstances",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "ec2:DescribeRegions",
        "lambda:ListFunctions",
        "lambda:GetFunction",
        "lambda:ListTags",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "s3:GetBucketAcl",
        "s3:GetBucketPolicy",
        "s3:GetEncryptionConfiguration",
        "s3:GetBucketVersioning",
        "rds:DescribeDBInstances",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Testing AWS Connection

### Using AWS CLI

```bash
# Test IAM access
aws iam list-users --max-items 1

# Test EC2 access
aws ec2 describe-instances --max-results 5

# Test Lambda access
aws lambda list-functions --max-items 1

# Test S3 access
aws s3 ls
```

### Using CIEM Tool

```bash
# Start the backend
cd backend
python -m uvicorn src.api.app:app --reload

# Test connection
curl http://localhost:8000/api/v1/aws/test
```

Expected response:
```json
{
  "success": true,
  "account_id": "123456789012",
  "regions": ["us-east-1", "us-west-2", ...],
  "permissions": {
    "iam": true,
    "ec2": true,
    "lambda": true
  }
}
```

---

## Troubleshooting

### Error: "Unable to locate credentials"

**Solution**: Ensure credentials are set in one of these locations:
1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. AWS credentials file (`~/.aws/credentials`)
3. IAM role (for EC2/ECS/Lambda)

### Error: "Access Denied"

**Solution**: Verify IAM permissions:
```bash
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:user/ciem-tool-scanner \
  --action-names iam:ListUsers ec2:DescribeInstances \
  --profile ciem-tool
```

### Error: "Region not found"

**Solution**: Set default region:
```bash
export AWS_DEFAULT_REGION=us-east-1
```

### Error: "Rate limit exceeded"

**Solution**: The tool automatically handles rate limiting with exponential backoff. If issues persist, reduce `MAX_CONCURRENT_REGIONS` in `.env`.

---

## Security Best Practices

1. **Rotate Access Keys**: Rotate keys every 90 days
2. **Use IAM Roles**: Prefer IAM roles over access keys in production
3. **Enable MFA**: Enable MFA for IAM users
4. **Least Privilege**: Use minimal permissions required
5. **Monitor Usage**: Enable CloudTrail to monitor API calls
6. **Secure Storage**: Never commit credentials to Git
7. **Use Secrets Manager**: Store credentials in AWS Secrets Manager for production

---

## Next Steps

After setting up AWS credentials:

1. [Run your first scan](USER_GUIDE.md#running-first-scan)
2. [Explore the dashboard](USER_GUIDE.md#dashboard-overview)
3. [Review risk findings](USER_GUIDE.md#risk-analysis)
4. [Generate compliance reports](USER_GUIDE.md#compliance-reports)

---

**Need Help?**
- [GitHub Issues](https://github.com/TechFxSolutions/aws-ciem-tool/issues)
- [Documentation](https://github.com/TechFxSolutions/aws-ciem-tool/docs)
