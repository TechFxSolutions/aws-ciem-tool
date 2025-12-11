#!/bin/bash

###############################################################################
# AWS CIEM Tool - AWS Resources Cleanup Script
# 
# IMPORTANT: This script is for FUTURE USE when the tool creates AWS resources.
# 
# Currently, the CIEM tool does NOT create any AWS resources. It only reads
# existing resources in your AWS account.
#
# This script is provided for future functionality when auto-remediation or
# test environment creation features are added.
#
# Usage: ./scripts/aws-cleanup.sh --region us-east-1 --profile default
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_TAG_KEY="Project"
PROJECT_TAG_VALUE="AWS-CIEM-Tool"
AWS_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
AWS_PROFILE="${AWS_PROFILE:-default}"
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--region REGION] [--profile PROFILE] [--dry-run]"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     AWS CIEM Tool - AWS Resources Cleanup Script          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Region: $AWS_REGION"
echo "  Profile: $AWS_PROFILE"
echo "  Tag Key: $PROJECT_TAG_KEY"
echo "  Tag Value: $PROJECT_TAG_VALUE"
if [ "$DRY_RUN" = true ]; then
    echo -e "  Mode: ${YELLOW}DRY RUN (no resources will be deleted)${NC}"
else
    echo -e "  Mode: ${RED}LIVE (resources will be DELETED)${NC}"
fi
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    echo "Install it from: https://aws.amazon.com/cli/"
    exit 1
fi

# Verify AWS credentials
echo -e "${YELLOW}Verifying AWS credentials...${NC}"
if ! aws sts get-caller-identity --profile "$AWS_PROFILE" &> /dev/null; then
    echo -e "${RED}Error: Invalid AWS credentials${NC}"
    echo "Please configure AWS CLI with: aws configure --profile $AWS_PROFILE"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query Account --output text)
echo -e "${GREEN}✓ Connected to AWS Account: $ACCOUNT_ID${NC}"
echo ""

# Warning
echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║                        WARNING                             ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${RED}IMPORTANT: The CIEM tool currently does NOT create AWS resources.${NC}"
echo -e "${RED}This script will search for resources tagged with:${NC}"
echo -e "${RED}  $PROJECT_TAG_KEY = $PROJECT_TAG_VALUE${NC}"
echo ""
echo -e "${YELLOW}If you have manually created test resources with this tag,${NC}"
echo -e "${YELLOW}they will be deleted.${NC}"
echo ""

if [ "$DRY_RUN" = false ]; then
    read -p "Are you sure you want to continue? Type 'DELETE' to confirm: " -r
    echo ""
    if [[ ! $REPLY == "DELETE" ]]; then
        echo -e "${GREEN}Cleanup cancelled.${NC}"
        exit 0
    fi
fi

echo -e "${GREEN}Starting AWS resource discovery...${NC}"
echo ""

# Function to execute or simulate command
execute_command() {
    local cmd="$1"
    local description="$2"
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would execute: $description${NC}"
        echo -e "${BLUE}Command: $cmd${NC}"
    else
        echo -e "${YELLOW}Executing: $description${NC}"
        eval "$cmd"
        echo -e "${GREEN}✓ Done${NC}"
    fi
}

# Counter for found resources
TOTAL_RESOURCES=0

# 1. Find and delete EC2 instances
echo -e "${YELLOW}[1/8] Searching for EC2 instances...${NC}"
EC2_INSTANCES=$(aws ec2 describe-instances \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --filters "Name=tag:$PROJECT_TAG_KEY,Values=$PROJECT_TAG_VALUE" "Name=instance-state-name,Values=running,stopped" \
    --query 'Reservations[].Instances[].InstanceId' \
    --output text)

if [ -n "$EC2_INSTANCES" ]; then
    echo -e "${BLUE}Found EC2 instances: $EC2_INSTANCES${NC}"
    for instance in $EC2_INSTANCES; do
        execute_command "aws ec2 terminate-instances --region $AWS_REGION --profile $AWS_PROFILE --instance-ids $instance" "Terminating EC2 instance $instance"
        ((TOTAL_RESOURCES++))
    done
else
    echo -e "${GREEN}✓ No EC2 instances found${NC}"
fi
echo ""

# 2. Find and delete S3 buckets
echo -e "${YELLOW}[2/8] Searching for S3 buckets...${NC}"
S3_BUCKETS=$(aws s3api list-buckets \
    --profile "$AWS_PROFILE" \
    --query 'Buckets[].Name' \
    --output text)

for bucket in $S3_BUCKETS; do
    TAGS=$(aws s3api get-bucket-tagging --bucket "$bucket" --profile "$AWS_PROFILE" 2>/dev/null || echo "")
    if echo "$TAGS" | grep -q "$PROJECT_TAG_VALUE"; then
        echo -e "${BLUE}Found S3 bucket: $bucket${NC}"
        execute_command "aws s3 rm s3://$bucket --recursive --profile $AWS_PROFILE" "Emptying S3 bucket $bucket"
        execute_command "aws s3api delete-bucket --bucket $bucket --profile $AWS_PROFILE" "Deleting S3 bucket $bucket"
        ((TOTAL_RESOURCES++))
    fi
done

if [ $TOTAL_RESOURCES -eq 0 ]; then
    echo -e "${GREEN}✓ No S3 buckets found${NC}"
fi
echo ""

# 3. Find and delete RDS instances
echo -e "${YELLOW}[3/8] Searching for RDS instances...${NC}"
RDS_INSTANCES=$(aws rds describe-db-instances \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --query 'DBInstances[].DBInstanceIdentifier' \
    --output text 2>/dev/null || echo "")

for db in $RDS_INSTANCES; do
    TAGS=$(aws rds list-tags-for-resource \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" \
        --resource-name "arn:aws:rds:$AWS_REGION:$ACCOUNT_ID:db:$db" 2>/dev/null || echo "")
    
    if echo "$TAGS" | grep -q "$PROJECT_TAG_VALUE"; then
        echo -e "${BLUE}Found RDS instance: $db${NC}"
        execute_command "aws rds delete-db-instance --region $AWS_REGION --profile $AWS_PROFILE --db-instance-identifier $db --skip-final-snapshot" "Deleting RDS instance $db"
        ((TOTAL_RESOURCES++))
    fi
done

if [ $TOTAL_RESOURCES -eq 0 ]; then
    echo -e "${GREEN}✓ No RDS instances found${NC}"
fi
echo ""

# 4. Find and delete Lambda functions
echo -e "${YELLOW}[4/8] Searching for Lambda functions...${NC}"
LAMBDA_FUNCTIONS=$(aws lambda list-functions \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --query 'Functions[].FunctionName' \
    --output text 2>/dev/null || echo "")

for func in $LAMBDA_FUNCTIONS; do
    TAGS=$(aws lambda list-tags \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" \
        --resource "arn:aws:lambda:$AWS_REGION:$ACCOUNT_ID:function:$func" 2>/dev/null || echo "")
    
    if echo "$TAGS" | grep -q "$PROJECT_TAG_VALUE"; then
        echo -e "${BLUE}Found Lambda function: $func${NC}"
        execute_command "aws lambda delete-function --region $AWS_REGION --profile $AWS_PROFILE --function-name $func" "Deleting Lambda function $func"
        ((TOTAL_RESOURCES++))
    fi
done

if [ $TOTAL_RESOURCES -eq 0 ]; then
    echo -e "${GREEN}✓ No Lambda functions found${NC}"
fi
echo ""

# 5. Find and delete Security Groups
echo -e "${YELLOW}[5/8] Searching for Security Groups...${NC}"
SECURITY_GROUPS=$(aws ec2 describe-security-groups \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --filters "Name=tag:$PROJECT_TAG_KEY,Values=$PROJECT_TAG_VALUE" \
    --query 'SecurityGroups[?GroupName!=`default`].GroupId' \
    --output text 2>/dev/null || echo "")

if [ -n "$SECURITY_GROUPS" ]; then
    for sg in $SECURITY_GROUPS; do
        echo -e "${BLUE}Found Security Group: $sg${NC}"
        execute_command "aws ec2 delete-security-group --region $AWS_REGION --profile $AWS_PROFILE --group-id $sg" "Deleting Security Group $sg"
        ((TOTAL_RESOURCES++))
    done
else
    echo -e "${GREEN}✓ No Security Groups found${NC}"
fi
echo ""

# 6. Find and delete IAM Roles
echo -e "${YELLOW}[6/8] Searching for IAM Roles...${NC}"
IAM_ROLES=$(aws iam list-roles \
    --profile "$AWS_PROFILE" \
    --query 'Roles[].RoleName' \
    --output text 2>/dev/null || echo "")

for role in $IAM_ROLES; do
    TAGS=$(aws iam list-role-tags \
        --profile "$AWS_PROFILE" \
        --role-name "$role" 2>/dev/null || echo "")
    
    if echo "$TAGS" | grep -q "$PROJECT_TAG_VALUE"; then
        echo -e "${BLUE}Found IAM Role: $role${NC}"
        
        # Detach policies first
        ATTACHED_POLICIES=$(aws iam list-attached-role-policies --profile "$AWS_PROFILE" --role-name "$role" --query 'AttachedPolicies[].PolicyArn' --output text)
        for policy in $ATTACHED_POLICIES; do
            execute_command "aws iam detach-role-policy --profile $AWS_PROFILE --role-name $role --policy-arn $policy" "Detaching policy from role $role"
        done
        
        # Delete inline policies
        INLINE_POLICIES=$(aws iam list-role-policies --profile "$AWS_PROFILE" --role-name "$role" --query 'PolicyNames[]' --output text)
        for policy in $INLINE_POLICIES; do
            execute_command "aws iam delete-role-policy --profile $AWS_PROFILE --role-name $role --policy-name $policy" "Deleting inline policy from role $role"
        done
        
        execute_command "aws iam delete-role --profile $AWS_PROFILE --role-name $role" "Deleting IAM Role $role"
        ((TOTAL_RESOURCES++))
    fi
done

if [ $TOTAL_RESOURCES -eq 0 ]; then
    echo -e "${GREEN}✓ No IAM Roles found${NC}"
fi
echo ""

# 7. Find and delete IAM Users
echo -e "${YELLOW}[7/8] Searching for IAM Users...${NC}"
IAM_USERS=$(aws iam list-users \
    --profile "$AWS_PROFILE" \
    --query 'Users[].UserName' \
    --output text 2>/dev/null || echo "")

for user in $IAM_USERS; do
    TAGS=$(aws iam list-user-tags \
        --profile "$AWS_PROFILE" \
        --user-name "$user" 2>/dev/null || echo "")
    
    if echo "$TAGS" | grep -q "$PROJECT_TAG_VALUE"; then
        echo -e "${BLUE}Found IAM User: $user${NC}"
        
        # Delete access keys
        ACCESS_KEYS=$(aws iam list-access-keys --profile "$AWS_PROFILE" --user-name "$user" --query 'AccessKeyMetadata[].AccessKeyId' --output text)
        for key in $ACCESS_KEYS; do
            execute_command "aws iam delete-access-key --profile $AWS_PROFILE --user-name $user --access-key-id $key" "Deleting access key for user $user"
        done
        
        # Detach policies
        ATTACHED_POLICIES=$(aws iam list-attached-user-policies --profile "$AWS_PROFILE" --user-name "$user" --query 'AttachedPolicies[].PolicyArn' --output text)
        for policy in $ATTACHED_POLICIES; do
            execute_command "aws iam detach-user-policy --profile $AWS_PROFILE --user-name $user --policy-arn $policy" "Detaching policy from user $user"
        done
        
        # Delete inline policies
        INLINE_POLICIES=$(aws iam list-user-policies --profile "$AWS_PROFILE" --user-name "$user" --query 'PolicyNames[]' --output text)
        for policy in $INLINE_POLICIES; do
            execute_command "aws iam delete-user-policy --profile $AWS_PROFILE --user-name $user --policy-name $policy" "Deleting inline policy from user $user"
        done
        
        execute_command "aws iam delete-user --profile $AWS_PROFILE --user-name $user" "Deleting IAM User $user"
        ((TOTAL_RESOURCES++))
    fi
done

if [ $TOTAL_RESOURCES -eq 0 ]; then
    echo -e "${GREEN}✓ No IAM Users found${NC}"
fi
echo ""

# 8. Find and delete IAM Policies
echo -e "${YELLOW}[8/8] Searching for IAM Policies...${NC}"
IAM_POLICIES=$(aws iam list-policies \
    --profile "$AWS_PROFILE" \
    --scope Local \
    --query 'Policies[].Arn' \
    --output text 2>/dev/null || echo "")

for policy_arn in $IAM_POLICIES; do
    TAGS=$(aws iam list-policy-tags \
        --profile "$AWS_PROFILE" \
        --policy-arn "$policy_arn" 2>/dev/null || echo "")
    
    if echo "$TAGS" | grep -q "$PROJECT_TAG_VALUE"; then
        echo -e "${BLUE}Found IAM Policy: $policy_arn${NC}"
        
        # Delete all policy versions except default
        VERSIONS=$(aws iam list-policy-versions --profile "$AWS_PROFILE" --policy-arn "$policy_arn" --query 'Versions[?!IsDefaultVersion].VersionId' --output text)
        for version in $VERSIONS; do
            execute_command "aws iam delete-policy-version --profile $AWS_PROFILE --policy-arn $policy_arn --version-id $version" "Deleting policy version $version"
        done
        
        execute_command "aws iam delete-policy --profile $AWS_PROFILE --policy-arn $policy_arn" "Deleting IAM Policy $policy_arn"
        ((TOTAL_RESOURCES++))
    fi
done

if [ $TOTAL_RESOURCES -eq 0 ]; then
    echo -e "${GREEN}✓ No IAM Policies found${NC}"
fi
echo ""

# Summary
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  Cleanup Complete!                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN: No resources were actually deleted.${NC}"
    echo -e "${YELLOW}Found $TOTAL_RESOURCES resources that would be deleted.${NC}"
    echo ""
    echo -e "${GREEN}To actually delete resources, run without --dry-run flag:${NC}"
    echo "  ./scripts/aws-cleanup.sh --region $AWS_REGION --profile $AWS_PROFILE"
else
    echo -e "${GREEN}Successfully processed $TOTAL_RESOURCES AWS resources.${NC}"
fi
echo ""

echo -e "${BLUE}Note: This script only deletes resources tagged with:${NC}"
echo -e "${BLUE}  $PROJECT_TAG_KEY = $PROJECT_TAG_VALUE${NC}"
echo ""
