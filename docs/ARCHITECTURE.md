# AWS CIEM Tool - Architecture Documentation

## Overview

The AWS CIEM (Cloud Infrastructure Entitlement Management) Tool is a comprehensive security platform designed to discover, analyze, and visualize AWS identities, permissions, and resource relationships.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Dashboard │  │Identity  │  │Risk View │  │Graph View│   │
│  │          │  │Explorer  │  │          │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓ REST API
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API Layer                                           │   │
│  │  /api/v1/scan, /api/v1/risks, /api/v1/graph        │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Business Logic                                      │   │
│  │  - IAM Discoverer                                    │   │
│  │  - Resource Discoverer                               │   │
│  │  - Risk Analyzer                                     │   │
│  │  - Relationship Builder                              │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────┐         ┌─────────────────────┐
│  PostgreSQL          │         │  Neo4j Graph DB     │
│  (Metadata Storage)  │         │  (Relationships)    │
│  - Scan results      │         │  - Identity graph   │
│  - Risk scores       │         │  - Resource graph   │
│  - Audit logs        │         │  - Access paths     │
└──────────────────────┘         └─────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      AWS APIs                               │
│  IAM | EC2 | Lambda | S3 | RDS | VPC | CloudTrail         │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend (React + TypeScript)

**Technology Stack:**
- React 18 with TypeScript
- Tailwind CSS for styling
- D3.js for graph visualization
- Cytoscape.js for network diagrams
- Recharts for analytics
- Axios for API calls

**Key Components:**
- **Dashboard**: Overview of risks, compliance, and statistics
- **Identity Explorer**: Browse IAM users, roles, and groups
- **Risk View**: Detailed risk analysis and remediation
- **Graph View**: Interactive visualization of relationships
- **Compliance View**: Compliance framework mapping

### 2. Backend (FastAPI + Python)

**Technology Stack:**
- FastAPI for REST API
- Boto3 for AWS SDK
- SQLAlchemy for PostgreSQL ORM
- Neo4j Python driver for graph database
- Celery for background tasks
- Pydantic for data validation

**Core Modules:**

#### Discoverers
- **IAM Discoverer**: Discovers users, roles, groups, policies
- **Resource Discoverer**: Discovers EC2, Lambda, S3, RDS, Security Groups
- **Network Discoverer**: Discovers VPCs, subnets, NACLs

#### Analyzers
- **Risk Analyzer**: Calculates risk scores and identifies threats
- **Permission Analyzer**: Evaluates effective permissions
- **Compliance Analyzer**: Maps to compliance frameworks
- **Relationship Builder**: Builds identity-resource-network graph

#### API Routes
```
/api/v1/
├── health                    # Health check
├── aws/
│   ├── test                  # Test AWS connection
│   └── regions               # List available regions
├── scan/
│   ├── start                 # Start discovery scan
│   ├── status/{scan_id}      # Get scan status
│   └── results/{scan_id}     # Get scan results
├── identities/
│   ├── users                 # List IAM users
│   ├── roles                 # List IAM roles
│   ├── groups                # List IAM groups
│   └── {id}/permissions      # Get effective permissions
├── resources/
│   ├── ec2                   # List EC2 instances
│   ├── lambda                # List Lambda functions
│   ├── s3                    # List S3 buckets
│   ├── rds                   # List RDS instances
│   └── security-groups       # List security groups
├── risks/
│   ├── summary               # Risk summary
│   ├── list                  # List all risks
│   ├── {risk_id}             # Get risk details
│   └── blast-radius/{arn}    # Calculate blast radius
├── relationships/
│   ├── graph                 # Get graph data
│   ├── role/{role_name}      # Get role relationships
│   └── security-group/{sg_id} # Get SG relationships
└── compliance/
    ├── frameworks            # List frameworks
    ├── checks                # Run compliance checks
    └── report                # Generate compliance report
```

### 3. Data Storage

#### PostgreSQL
Stores structured data:
- Scan metadata and history
- Risk assessments
- Compliance check results
- User audit logs
- Configuration settings

**Schema:**
```sql
-- Scans table
CREATE TABLE scans (
    id UUID PRIMARY KEY,
    account_id VARCHAR(12),
    region VARCHAR(20),
    status VARCHAR(20),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    results JSONB
);

-- Risks table
CREATE TABLE risks (
    id UUID PRIMARY KEY,
    scan_id UUID REFERENCES scans(id),
    risk_type VARCHAR(50),
    severity VARCHAR(20),
    risk_score INTEGER,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details JSONB,
    created_at TIMESTAMP
);

-- Identities table
CREATE TABLE identities (
    id UUID PRIMARY KEY,
    account_id VARCHAR(12),
    identity_type VARCHAR(20),
    identity_name VARCHAR(255),
    arn VARCHAR(512),
    details JSONB,
    last_scanned TIMESTAMP
);
```

#### Neo4j Graph Database
Stores relationship data:
- Identity → Permission → Resource paths
- Security Group → Resource connections
- Cross-account trust relationships
- Privilege escalation paths

**Graph Model:**
```cypher
// Nodes
(:IAMRole {name, arn, is_admin})
(:IAMUser {name, arn, mfa_enabled})
(:EC2Instance {id, name, is_public})
(:Lambda {name, runtime})
(:SecurityGroup {id, name, has_internet_access})
(:S3Bucket {name, is_public})
(:Internet {cidr: "0.0.0.0/0"})

// Relationships
(:IAMRole)-[:ASSUMES_ROLE]->(:EC2Instance)
(:IAMRole)-[:EXECUTION_ROLE]->(:Lambda)
(:EC2Instance)-[:PROTECTED_BY]->(:SecurityGroup)
(:SecurityGroup)-[:ALLOWS_TRAFFIC_FROM]->(:Internet)
(:IAMRole)-[:HAS_POLICY]->(:Policy)
```

## Data Flow

### Discovery Flow
```
1. User triggers scan via UI
2. Backend creates scan job
3. Discoverers run in parallel:
   - IAM Discoverer → List users, roles, groups
   - Resource Discoverer → List EC2, Lambda, S3, RDS
   - Network Discoverer → List Security Groups, VPCs
4. Results stored in PostgreSQL
5. Relationships built and stored in Neo4j
6. Risk analysis performed
7. Results returned to UI
```

### Risk Analysis Flow
```
1. Fetch IAM and resource data
2. Analyze identity risks:
   - Users without MFA
   - Inactive users
   - Admin roles
3. Analyze resource risks:
   - Public EC2 instances
   - Public S3 buckets
   - Unencrypted resources
4. Analyze network risks:
   - Security groups with 0.0.0.0/0
   - Open critical ports
5. Calculate risk scores
6. Store in database
7. Return prioritized risk list
```

### Graph Visualization Flow
```
1. Fetch relationship data from Neo4j
2. Transform to D3.js/Cytoscape format
3. Apply layout algorithm
4. Add risk indicators (colors)
5. Enable interactive exploration
6. Support drill-down navigation
```

## Hierarchical Structure (CIEM Diagram Implementation)

### Level 1: Consolidated View
All resources grouped by IAM role with risk scoring

### Level 2: Resource Grouping
- Level 2.0: Resources by Security Group
- Level 2.1: Resources in specific Security Group
- Level 2.2: Risky resources (Internet accessible)
- Level 2.3: Alternative Internet paths

### Level 3: Security Groups
Security group details with ingress/egress rules

### Level 4: IAM Roles
Individual IAM role with attached resources

### Level 5: Resources
Individual resource details (EC2, Lambda, etc.)

## Security Considerations

1. **Read-Only Access**: Tool requires only read permissions
2. **Credential Management**: Supports IAM roles, access keys, SSO
3. **Data Encryption**: All data encrypted at rest and in transit
4. **Audit Logging**: All actions logged for compliance
5. **RBAC**: Role-based access control for multi-user environments

## Scalability

- **Horizontal Scaling**: Backend can scale with multiple workers
- **Caching**: Redis for frequently accessed data
- **Async Processing**: Celery for background scans
- **Database Optimization**: Indexed queries, connection pooling
- **Multi-Region**: Parallel scanning across regions

## Deployment Options

1. **Local Development**: Docker Compose
2. **AWS ECS**: Containerized deployment
3. **Kubernetes**: For large-scale deployments
4. **Serverless**: Lambda + API Gateway (future)

## Monitoring & Observability

- **Metrics**: Prometheus for metrics collection
- **Logging**: Structured logging with Loguru
- **Tracing**: OpenTelemetry for distributed tracing
- **Alerting**: Integration with Slack, PagerDuty

## Future Enhancements

### Phase 2
- Unused permission detection
- Privilege escalation path detection
- Cross-account analysis
- ML-based anomaly detection

### Phase 3
- Least privilege policy generation
- Automated remediation
- JIT access provisioning
- Multi-cloud support (Azure, GCP)

## Performance Benchmarks

- **IAM Discovery**: ~1000 identities/minute
- **Resource Discovery**: ~500 resources/minute per region
- **Risk Analysis**: ~10,000 resources/minute
- **Graph Building**: ~5,000 relationships/minute

## API Rate Limits

AWS API rate limits are handled with:
- Exponential backoff
- Request throttling
- Batch operations where possible
- Caching of static data

## Compliance Frameworks Supported

- CIS AWS Foundations Benchmark
- NIST 800-53
- ISO 27001
- PCI-DSS
- HIPAA
- SOC 2

---

**Last Updated**: 2025-12-11
**Version**: 0.1.0
