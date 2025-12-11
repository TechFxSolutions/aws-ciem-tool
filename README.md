# AWS CIEM Tool

**Cloud Infrastructure Entitlement Management (CIEM) for AWS**

A comprehensive security platform for discovering identities, analyzing permissions, assessing risks, and visualizing access relationships across your AWS infrastructure.

## 🎯 Features

### Phase 1 (MVP) - Current
- ✅ **Identity Discovery**: IAM Users, Roles, Groups, Service Accounts
- ✅ **Resource Discovery**: EC2, Lambda, S3, RDS, Security Groups
- ✅ **Permission Analysis**: Effective permissions, policy evaluation
- ✅ **Risk Assessment**: Over-privileged identities, Internet exposure, dormant accounts
- ✅ **Interactive Graph UI**: Visualize identity → permission → resource relationships
- ✅ **Compliance Checks**: CIS AWS Foundations Benchmark

### Phase 2 (Planned)
- 🔄 Unused permission detection (AWS Access Advisor)
- 🔄 Privilege escalation path detection
- 🔄 Cross-account access analysis
- 🔄 ML-based anomaly detection

### Phase 3 (Future)
- 📋 Least privilege policy generation
- 📋 Automated remediation workflows
- 📋 JIT (Just-In-Time) access provisioning
- 📋 Multi-cloud support (Azure, GCP)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                     │
│  Dashboard | Identity Explorer | Risk View | Graph View │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                      │
│  Discovery | Analysis | Risk Scoring | API Endpoints   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────┐         ┌─────────────────────┐
│  PostgreSQL          │         │  Neo4j Graph DB     │
│  (Metadata Storage)  │         │  (Relationships)    │
└──────────────────────┘         └─────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                      AWS APIs                           │
│  IAM | EC2 | Lambda | S3 | RDS | VPC | CloudTrail     │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Docker & Docker Compose
- AWS Account with ReadOnly access

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/TechFxSolutions/aws-ciem-tool.git
cd aws-ciem-tool
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your AWS credentials and configuration
```

3. **Start with Docker Compose**
```bash
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Setup (Development)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.api.app:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

## 📖 Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [AWS Setup Guide](docs/AWS_SETUP.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [User Guide](docs/USER_GUIDE.md)
- [Security Best Practices](docs/SECURITY.md)

## 🔐 AWS Permissions

The tool requires **read-only** access to your AWS account. Recommended IAM policy:

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
        "cloudtrail:LookupEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

## 🎨 UI Screenshots

### Dashboard
![Dashboard](docs/images/dashboard.png)

### Identity Graph
![Graph View](docs/images/graph-view.png)

### Risk Assessment
![Risk Dashboard](docs/images/risk-dashboard.png)

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

## 📊 Use Cases

1. **Security Audits**: Identify over-privileged identities and excessive permissions
2. **Compliance**: Map to CIS, NIST, ISO 27001 frameworks
3. **Incident Response**: Quickly assess blast radius of compromised credentials
4. **Access Reviews**: Periodic review of who has access to what
5. **Least Privilege**: Generate right-sized IAM policies

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.9+, Boto3
- **Frontend**: React 18, TypeScript, Tailwind CSS
- **Databases**: PostgreSQL 14, Neo4j 5
- **Visualization**: D3.js, Cytoscape.js, Recharts
- **Deployment**: Docker, Docker Compose

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- AWS IAM Policy Simulator
- OWASP Cloud Security Project
- CIS AWS Foundations Benchmark

## 📧 Contact

- **Project**: [GitHub Repository](https://github.com/TechFxSolutions/aws-ciem-tool)
- **Issues**: [Report Bug](https://github.com/TechFxSolutions/aws-ciem-tool/issues)
- **Discussions**: [GitHub Discussions](https://github.com/TechFxSolutions/aws-ciem-tool/discussions)

---

**⚠️ Security Notice**: This tool requires AWS credentials with read access. Never commit credentials to the repository. Use environment variables or AWS IAM roles.

**Built with ❤️ for Cloud Security**
