#!/bin/bash

# Scan Failure Diagnostic Script
# Helps identify why scans are failing

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     AWS CIEM Tool - Scan Failure Diagnostic               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print section header
print_section() {
    echo -e "\n${BLUE}═══ $1 ═══${NC}\n"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print error
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check 1: Docker Status
print_section "1. Docker Container Status"
if docker-compose ps > /dev/null 2>&1; then
    docker-compose ps
    
    # Check if backend is running
    if docker-compose ps | grep -q "ciem-backend.*Up"; then
        print_success "Backend container is running"
    else
        print_error "Backend container is not running"
        echo "  Run: docker-compose up -d backend"
    fi
else
    print_error "Docker Compose not available or not in project directory"
    exit 1
fi

# Check 2: Environment Variables
print_section "2. Environment Variables"
if [ -f .env ]; then
    print_success ".env file exists"
    
    # Check AWS credentials
    if grep -q "AWS_ACCESS_KEY_ID=" .env; then
        AWS_KEY=$(grep "AWS_ACCESS_KEY_ID=" .env | cut -d'=' -f2)
        if [ "$AWS_KEY" = "your_access_key_here" ] || [ -z "$AWS_KEY" ]; then
            print_error "AWS_ACCESS_KEY_ID is not set (still placeholder)"
            echo "  Edit .env and add your actual AWS access key"
        else
            print_success "AWS_ACCESS_KEY_ID is set"
        fi
    else
        print_error "AWS_ACCESS_KEY_ID not found in .env"
    fi
    
    if grep -q "AWS_SECRET_ACCESS_KEY=" .env; then
        AWS_SECRET=$(grep "AWS_SECRET_ACCESS_KEY=" .env | cut -d'=' -f2)
        if [ "$AWS_SECRET" = "your_secret_key_here" ] || [ -z "$AWS_SECRET" ]; then
            print_error "AWS_SECRET_ACCESS_KEY is not set (still placeholder)"
            echo "  Edit .env and add your actual AWS secret key"
        else
            print_success "AWS_SECRET_ACCESS_KEY is set"
        fi
    else
        print_error "AWS_SECRET_ACCESS_KEY not found in .env"
    fi
    
    if grep -q "AWS_DEFAULT_REGION=" .env; then
        print_success "AWS_DEFAULT_REGION is set"
    else
        print_warning "AWS_DEFAULT_REGION not found in .env (will use default)"
    fi
else
    print_error ".env file not found"
    echo "  Run: cp .env.example .env"
    echo "  Then edit .env with your AWS credentials"
    exit 1
fi

# Check 3: Backend Health
print_section "3. Backend Health Check"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    HEALTH=$(curl -s http://localhost:8000/health)
    print_success "Backend is responding"
    echo "  Response: $HEALTH"
else
    print_error "Backend is not responding"
    echo "  Check backend logs: docker-compose logs backend"
fi

# Check 4: AWS Connection Test
print_section "4. AWS Connection Test"
AWS_TEST=$(curl -s http://localhost:8000/api/v1/aws/test 2>&1)
if echo "$AWS_TEST" | grep -q '"success":true'; then
    print_success "AWS connection successful"
    echo "$AWS_TEST" | python3 -m json.tool 2>/dev/null || echo "$AWS_TEST"
else
    print_error "AWS connection failed"
    echo "  Response: $AWS_TEST"
    echo ""
    echo "  Common causes:"
    echo "  - Invalid AWS credentials in .env"
    echo "  - IAM user lacks permissions"
    echo "  - AWS credentials not passed to container"
fi

# Check 5: Test AWS CLI from Container
print_section "5. AWS CLI Test (from container)"
if docker-compose exec -T backend aws sts get-caller-identity > /dev/null 2>&1; then
    print_success "AWS CLI works in container"
    docker-compose exec -T backend aws sts get-caller-identity
else
    print_error "AWS CLI failed in container"
    echo "  This confirms AWS credentials issue"
fi

# Check 6: Recent Backend Logs
print_section "6. Recent Backend Logs (last 30 lines)"
docker-compose logs --tail=30 backend

# Check 7: Look for Error Patterns
print_section "7. Error Pattern Analysis"
LOGS=$(docker-compose logs backend 2>&1)

if echo "$LOGS" | grep -qi "NoCredentialsError"; then
    print_error "Found: NoCredentialsError"
    echo "  → AWS credentials not found"
    echo "  → Fix: Update .env with valid credentials and restart backend"
fi

if echo "$LOGS" | grep -qi "InvalidAccessKeyId"; then
    print_error "Found: InvalidAccessKeyId"
    echo "  → AWS access key is invalid"
    echo "  → Fix: Verify access key in AWS Console and update .env"
fi

if echo "$LOGS" | grep -qi "SignatureDoesNotMatch"; then
    print_error "Found: SignatureDoesNotMatch"
    echo "  → AWS secret key is invalid"
    echo "  → Fix: Verify secret key in AWS Console and update .env"
fi

if echo "$LOGS" | grep -qi "AccessDenied\|UnauthorizedOperation"; then
    print_error "Found: AccessDenied or UnauthorizedOperation"
    echo "  → IAM user lacks required permissions"
    echo "  → Fix: Attach read-only policies to IAM user"
fi

if echo "$LOGS" | grep -qi "ConnectionError\|Timeout"; then
    print_error "Found: Connection or Timeout errors"
    echo "  → Network connectivity issue"
    echo "  → Fix: Check internet connection and AWS service status"
fi

# Summary
print_section "Summary & Next Steps"

echo "If scan is failing, check the following in order:"
echo ""
echo "1. ${YELLOW}Update .env with REAL AWS credentials${NC}"
echo "   nano .env"
echo ""
echo "2. ${YELLOW}Restart backend container${NC}"
echo "   docker-compose restart backend"
echo ""
echo "3. ${YELLOW}Test AWS connection${NC}"
echo "   curl http://localhost:8000/api/v1/aws/test"
echo ""
echo "4. ${YELLOW}Check IAM permissions${NC}"
echo "   Ensure user has read-only access to IAM, EC2, Lambda, S3, RDS"
echo ""
echo "5. ${YELLOW}Try minimal scan${NC}"
echo "   Scan only IAM in us-east-1 to isolate issue"
echo ""
echo "For detailed troubleshooting, see: ${BLUE}SCAN_FAILURE_FIX.md${NC}"
echo ""
