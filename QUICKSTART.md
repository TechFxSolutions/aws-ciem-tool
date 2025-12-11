# AWS CIEM Tool - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Docker & Docker Compose installed
- AWS Account with credentials
- 8GB RAM minimum

---

## Option 1: Docker Compose (Recommended)

### Step 1: Clone Repository
```bash
git clone https://github.com/TechFxSolutions/aws-ciem-tool.git
cd aws-ciem-tool
```

### Step 2: Configure Environment
```bash
cp .env.example .env
```

Edit `.env` and add your AWS credentials:
```bash
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
```

### Step 3: Start All Services
```bash
docker-compose up -d
```

This starts:
- ✅ PostgreSQL (port 5432)
- ✅ Neo4j (ports 7474, 7687)
- ✅ Redis (port 6379)
- ✅ Backend API (port 8000)
- ✅ Frontend UI (port 3000)

### Step 4: Access the Application
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474

### Step 5: Run Your First Scan
1. Open http://localhost:3000
2. Click "Start New Scan"
3. Select regions to scan
4. Wait for completion
5. View results in Dashboard

---

## Option 2: Manual Setup (Development)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env with your AWS credentials

# Start backend
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start frontend
npm start
```

Frontend will be available at: http://localhost:3000

---

## 🧪 Test the Setup

### 1. Test AWS Connection
```bash
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

### 2. Start a Scan via API
```bash
curl -X POST http://localhost:8000/api/v1/scan/start \
  -H "Content-Type: application/json" \
  -d '{
    "regions": ["us-east-1"],
    "scan_iam": true,
    "scan_ec2": true,
    "scan_lambda": true,
    "scan_s3": true,
    "scan_rds": true,
    "scan_security_groups": true
  }'
```

Response:
```json
{
  "scan_id": "abc123...",
  "status": "queued",
  "message": "Scan started successfully",
  "started_at": "2025-12-11T02:00:00Z"
}
```

### 3. Check Scan Status
```bash
curl http://localhost:8000/api/v1/scan/status/{scan_id}
```

### 4. Get Scan Results
```bash
curl http://localhost:8000/api/v1/scan/results/{scan_id}
```

---

## 📊 Using the UI

### Dashboard
- View risk summary (Critical, High, Medium, Low)
- See top risks
- Monitor recent scans
- Quick actions

### Graph View
- Interactive visualization of relationships
- IAM Roles → Resources → Security Groups
- Internet exposure paths
- Click nodes for details
- Export as PNG

### API Documentation
- Interactive API docs at http://localhost:8000/docs
- Try endpoints directly from browser
- View request/response schemas

---

## 🔍 Example Workflows

### Workflow 1: Security Audit
1. Start comprehensive scan (all regions)
2. Review risk summary on Dashboard
3. Filter critical risks
4. Investigate blast radius for admin roles
5. Export findings

### Workflow 2: Compliance Check
1. Run scan for specific region
2. View compliance risks
3. Check for:
   - Users without MFA
   - Public resources
   - Unencrypted data
4. Generate remediation plan

### Workflow 3: Access Analysis
1. Start scan
2. Open Graph View
3. Identify Internet-exposed resources
4. Trace access paths
5. Review security group rules

---

## 🛠️ Common Commands

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# View service status
docker-compose ps
```

### Backend

```bash
# Run backend directly
cd backend
uvicorn src.api.main:app --reload

# Run with specific host/port
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Check logs
tail -f logs/ciem_*.log
```

### Frontend

```bash
# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

---

## 📡 API Endpoints

### Scan Management
- `POST /api/v1/scan/start` - Start new scan
- `GET /api/v1/scan/status/{scan_id}` - Get scan status
- `GET /api/v1/scan/results/{scan_id}` - Get scan results
- `GET /api/v1/scan/list` - List all scans
- `DELETE /api/v1/scan/{scan_id}` - Delete scan

### Risk Analysis
- `GET /api/v1/risks/summary` - Risk summary
- `GET /api/v1/risks/list` - List all risks
- `GET /api/v1/risks/{risk_id}` - Risk details
- `GET /api/v1/risks/blast-radius/{arn}` - Blast radius
- `GET /api/v1/risks/statistics` - Risk statistics

### Relationships
- `GET /api/v1/relationships/graph` - Graph data
- `GET /api/v1/relationships/consolidated` - Consolidated view
- `GET /api/v1/relationships/role/{name}` - Role relationships
- `GET /api/v1/relationships/security-group/{id}` - SG relationships
- `GET /api/v1/relationships/internet-exposed` - Internet-exposed resources

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check AWS credentials
aws sts get-caller-identity
```

### Frontend won't start
```bash
# Clear node_modules
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 16+
```

### Docker issues
```bash
# Remove all containers and volumes
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

### AWS connection fails
- Verify credentials in `.env`
- Check IAM permissions
- Test with AWS CLI: `aws iam list-users`

### Scan takes too long
- Reduce number of regions
- Disable unnecessary resource types
- Check AWS API rate limits

---

## 📚 Next Steps

1. **Read Documentation**
   - [Architecture Guide](docs/ARCHITECTURE.md)
   - [AWS Setup Guide](docs/AWS_SETUP.md)
   - [Project Status](PROJECT_STATUS.md)

2. **Explore Features**
   - Run scans across multiple regions
   - Analyze risk patterns
   - Visualize relationships
   - Export reports

3. **Customize**
   - Adjust risk thresholds in `.env`
   - Add custom compliance checks
   - Extend discovery modules

4. **Contribute**
   - Report issues on GitHub
   - Submit pull requests
   - Share feedback

---

## 🆘 Getting Help

- **GitHub Issues**: https://github.com/TechFxSolutions/aws-ciem-tool/issues
- **Documentation**: https://github.com/TechFxSolutions/aws-ciem-tool/docs
- **API Docs**: http://localhost:8000/docs (when running)

---

## ⚡ Performance Tips

1. **Scan Optimization**
   - Start with single region
   - Enable only needed resource types
   - Use `MAX_CONCURRENT_REGIONS=3` in `.env`

2. **Database**
   - PostgreSQL: Increase `shared_buffers` for large datasets
   - Neo4j: Adjust heap size in docker-compose.yml

3. **Caching**
   - Redis caches frequently accessed data
   - Results stored for 24 hours by default

---

**Ready to secure your AWS infrastructure? Start scanning now!** 🚀
