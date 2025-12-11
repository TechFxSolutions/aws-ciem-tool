"""
Risk Analysis Module
Analyzes security risks based on IAM permissions, resource exposure, and compliance
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..utils import settings, app_logger as logger


class RiskAnalyzer:
    """Analyzes security risks across AWS resources"""
    
    def __init__(self):
        self.risk_scores = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
    
    def analyze_all(self, iam_data: Dict, resource_data: Dict) -> Dict[str, Any]:
        """
        Perform comprehensive risk analysis
        
        Args:
            iam_data: IAM discovery results
            resource_data: Resource discovery results
        
        Returns:
            Dictionary containing risk analysis results
        """
        logger.info("Starting risk analysis")
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": iam_data.get("account_id"),
            "region": resource_data.get("region"),
            "risks": {
                "identity_risks": self.analyze_identity_risks(iam_data),
                "resource_risks": self.analyze_resource_risks(resource_data),
                "network_risks": self.analyze_network_risks(resource_data),
                "compliance_risks": self.analyze_compliance_risks(iam_data, resource_data),
            },
            "risk_summary": {},
            "top_risks": [],
        }
        
        # Compile all risks
        all_risks = []
        for category, risks in results["risks"].items():
            all_risks.extend(risks)
        
        # Sort by risk score
        all_risks.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
        
        # Categorize risks
        for risk in all_risks:
            score = risk.get("risk_score", 0)
            if score >= settings.risk_critical_threshold:
                self.risk_scores["critical"].append(risk)
            elif score >= settings.risk_high_threshold:
                self.risk_scores["high"].append(risk)
            elif score >= settings.risk_medium_threshold:
                self.risk_scores["medium"].append(risk)
            else:
                self.risk_scores["low"].append(risk)
        
        # Add summary
        results["risk_summary"] = {
            "total_risks": len(all_risks),
            "critical": len(self.risk_scores["critical"]),
            "high": len(self.risk_scores["high"]),
            "medium": len(self.risk_scores["medium"]),
            "low": len(self.risk_scores["low"]),
        }
        
        # Top 10 risks
        results["top_risks"] = all_risks[:10]
        
        logger.info(f"Risk analysis completed: {results['risk_summary']}")
        return results
    
    def analyze_identity_risks(self, iam_data: Dict) -> List[Dict[str, Any]]:
        """Analyze IAM identity-related risks"""
        logger.info("Analyzing identity risks")
        risks = []
        
        # Check for users without MFA
        for user in iam_data.get("users", []):
            if not user.get("mfa_enabled"):
                risks.append({
                    "risk_id": f"IAM-USER-MFA-{user['username']}",
                    "risk_type": "identity",
                    "severity": "high",
                    "risk_score": 75,
                    "title": f"User without MFA: {user['username']}",
                    "description": "IAM user does not have MFA enabled, increasing risk of credential compromise",
                    "resource_type": "iam_user",
                    "resource_id": user['username'],
                    "resource_arn": user.get('arn'),
                    "remediation": "Enable MFA for this user",
                    "compliance_frameworks": ["CIS-1.2", "NIST-800-53"],
                })
        
        # Check for inactive users
        for user in iam_data.get("users", []):
            if user.get("is_inactive"):
                risks.append({
                    "risk_id": f"IAM-USER-INACTIVE-{user['username']}",
                    "risk_type": "identity",
                    "severity": "medium",
                    "risk_score": 60,
                    "title": f"Inactive user: {user['username']}",
                    "description": f"User has not logged in for {user.get('days_since_login', 'unknown')} days",
                    "resource_type": "iam_user",
                    "resource_id": user['username'],
                    "resource_arn": user.get('arn'),
                    "remediation": "Review and disable or delete inactive users",
                    "compliance_frameworks": ["CIS-1.3"],
                })
        
        # Check for admin roles
        for role in iam_data.get("roles", []):
            if role.get("is_admin"):
                risks.append({
                    "risk_id": f"IAM-ROLE-ADMIN-{role['role_name']}",
                    "risk_type": "identity",
                    "severity": "high",
                    "risk_score": 80,
                    "title": f"Admin role: {role['role_name']}",
                    "description": "Role has administrative access which should be carefully monitored",
                    "resource_type": "iam_role",
                    "resource_id": role['role_name'],
                    "resource_arn": role.get('arn'),
                    "remediation": "Review admin access and apply least privilege principle",
                    "compliance_frameworks": ["CIS-1.16"],
                })
        
        # Check for users with access keys
        for user in iam_data.get("users", []):
            active_keys = [k for k in user.get("access_keys", []) if k['status'] == 'Active']
            if len(active_keys) > 1:
                risks.append({
                    "risk_id": f"IAM-USER-MULTIKEY-{user['username']}",
                    "risk_type": "identity",
                    "severity": "medium",
                    "risk_score": 55,
                    "title": f"Multiple active access keys: {user['username']}",
                    "description": f"User has {len(active_keys)} active access keys",
                    "resource_type": "iam_user",
                    "resource_id": user['username'],
                    "resource_arn": user.get('arn'),
                    "remediation": "Rotate and remove unnecessary access keys",
                    "compliance_frameworks": ["CIS-1.4"],
                })
        
        logger.info(f"Found {len(risks)} identity risks")
        return risks
    
    def analyze_resource_risks(self, resource_data: Dict) -> List[Dict[str, Any]]:
        """Analyze resource-related risks"""
        logger.info("Analyzing resource risks")
        risks = []
        
        # Check for public EC2 instances
        for instance in resource_data.get("ec2_instances", []):
            if instance.get("is_public"):
                # Check if it has risky security groups
                has_risky_sg = False
                for sg in instance.get("security_groups", []):
                    # We'll need to cross-reference with security group data
                    has_risky_sg = True  # Simplified for now
                
                risk_score = 90 if has_risky_sg else 70
                
                risks.append({
                    "risk_id": f"EC2-PUBLIC-{instance['instance_id']}",
                    "risk_type": "resource",
                    "severity": "critical" if has_risky_sg else "high",
                    "risk_score": risk_score,
                    "title": f"Public EC2 instance: {instance['name']}",
                    "description": "EC2 instance is publicly accessible from the Internet",
                    "resource_type": "ec2_instance",
                    "resource_id": instance['instance_id'],
                    "resource_name": instance['name'],
                    "iam_role": instance.get('iam_instance_profile'),
                    "security_groups": [sg['group_id'] for sg in instance.get('security_groups', [])],
                    "remediation": "Review security groups and remove public access if not required",
                    "compliance_frameworks": ["CIS-5.1"],
                })
        
        # Check for public S3 buckets
        for bucket in resource_data.get("s3_buckets", []):
            if bucket.get("is_public"):
                risks.append({
                    "risk_id": f"S3-PUBLIC-{bucket['bucket_name']}",
                    "risk_type": "resource",
                    "severity": "critical",
                    "risk_score": 95,
                    "title": f"Public S3 bucket: {bucket['bucket_name']}",
                    "description": "S3 bucket is publicly accessible",
                    "resource_type": "s3_bucket",
                    "resource_id": bucket['bucket_name'],
                    "remediation": "Enable S3 Block Public Access and review bucket policies",
                    "compliance_frameworks": ["CIS-2.1.5"],
                })
        
        # Check for unencrypted S3 buckets
        for bucket in resource_data.get("s3_buckets", []):
            if not bucket.get("encryption_enabled"):
                risks.append({
                    "risk_id": f"S3-UNENCRYPTED-{bucket['bucket_name']}",
                    "risk_type": "resource",
                    "severity": "high",
                    "risk_score": 75,
                    "title": f"Unencrypted S3 bucket: {bucket['bucket_name']}",
                    "description": "S3 bucket does not have encryption enabled",
                    "resource_type": "s3_bucket",
                    "resource_id": bucket['bucket_name'],
                    "remediation": "Enable default encryption for the bucket",
                    "compliance_frameworks": ["CIS-2.1.1"],
                })
        
        # Check for publicly accessible RDS instances
        for instance in resource_data.get("rds_instances", []):
            if instance.get("publicly_accessible"):
                risks.append({
                    "risk_id": f"RDS-PUBLIC-{instance['db_instance_identifier']}",
                    "risk_type": "resource",
                    "severity": "critical",
                    "risk_score": 90,
                    "title": f"Public RDS instance: {instance['db_instance_identifier']}",
                    "description": "RDS instance is publicly accessible from the Internet",
                    "resource_type": "rds_instance",
                    "resource_id": instance['db_instance_identifier'],
                    "remediation": "Disable public accessibility and use VPC peering or VPN",
                    "compliance_frameworks": ["CIS-2.3.1"],
                })
        
        # Check for unencrypted RDS instances
        for instance in resource_data.get("rds_instances", []):
            if not instance.get("encrypted"):
                risks.append({
                    "risk_id": f"RDS-UNENCRYPTED-{instance['db_instance_identifier']}",
                    "risk_type": "resource",
                    "severity": "high",
                    "risk_score": 75,
                    "title": f"Unencrypted RDS instance: {instance['db_instance_identifier']}",
                    "description": "RDS instance does not have encryption enabled",
                    "resource_type": "rds_instance",
                    "resource_id": instance['db_instance_identifier'],
                    "remediation": "Enable encryption for the RDS instance",
                    "compliance_frameworks": ["CIS-2.3.1"],
                })
        
        logger.info(f"Found {len(risks)} resource risks")
        return risks
    
    def analyze_network_risks(self, resource_data: Dict) -> List[Dict[str, Any]]:
        """Analyze network-related risks (Security Groups)"""
        logger.info("Analyzing network risks")
        risks = []
        
        # Check for security groups with Internet access
        for sg in resource_data.get("security_groups", []):
            if sg.get("has_internet_access"):
                risky_rules = sg.get("risky_rules", [])
                
                # Calculate risk score based on exposed ports
                risk_score = 85
                severity = "high"
                
                # Check for critical ports
                critical_ports = [22, 3389, 1433, 3306, 5432, 27017]
                for rule in risky_rules:
                    if rule.get('from_port') in critical_ports:
                        risk_score = 95
                        severity = "critical"
                        break
                
                risks.append({
                    "risk_id": f"SG-INTERNET-{sg['group_id']}",
                    "risk_type": "network",
                    "severity": severity,
                    "risk_score": risk_score,
                    "title": f"Security group with Internet access: {sg['group_name']}",
                    "description": f"Security group allows inbound traffic from 0.0.0.0/0",
                    "resource_type": "security_group",
                    "resource_id": sg['group_id'],
                    "resource_name": sg['group_name'],
                    "vpc_id": sg.get('vpc_id'),
                    "risky_rules": risky_rules,
                    "remediation": "Restrict security group rules to specific IP ranges",
                    "compliance_frameworks": ["CIS-5.2"],
                })
        
        logger.info(f"Found {len(risks)} network risks")
        return risks
    
    def analyze_compliance_risks(self, iam_data: Dict, resource_data: Dict) -> List[Dict[str, Any]]:
        """Analyze compliance-related risks"""
        logger.info("Analyzing compliance risks")
        risks = []
        
        if not settings.enable_cis_benchmark:
            return risks
        
        # CIS Benchmark checks
        
        # Check for root account usage
        # This would require CloudTrail data - placeholder for now
        
        # Check for password policy
        # This would require IAM password policy check - placeholder for now
        
        logger.info(f"Found {len(risks)} compliance risks")
        return risks
    
    def calculate_blast_radius(self, identity_arn: str, iam_data: Dict, resource_data: Dict) -> Dict[str, Any]:
        """
        Calculate the blast radius if an identity is compromised
        
        Args:
            identity_arn: ARN of the IAM identity
            iam_data: IAM discovery results
            resource_data: Resource discovery results
        
        Returns:
            Dictionary with blast radius analysis
        """
        logger.info(f"Calculating blast radius for {identity_arn}")
        
        blast_radius = {
            "identity_arn": identity_arn,
            "affected_resources": [],
            "permissions": [],
            "risk_score": 0,
        }
        
        # Find the identity
        identity = None
        identity_type = None
        
        # Check if it's a role
        for role in iam_data.get("roles", []):
            if role.get("arn") == identity_arn:
                identity = role
                identity_type = "role"
                break
        
        # Check if it's a user
        if not identity:
            for user in iam_data.get("users", []):
                if user.get("arn") == identity_arn:
                    identity = user
                    identity_type = "user"
                    break
        
        if not identity:
            logger.warning(f"Identity not found: {identity_arn}")
            return blast_radius
        
        # Find resources using this identity
        if identity_type == "role":
            role_name = identity.get("role_name")
            
            # Check EC2 instances
            for instance in resource_data.get("ec2_instances", []):
                if instance.get("iam_instance_profile") == role_name:
                    blast_radius["affected_resources"].append({
                        "resource_type": "ec2_instance",
                        "resource_id": instance["instance_id"],
                        "resource_name": instance["name"],
                        "is_public": instance.get("is_public"),
                    })
            
            # Check Lambda functions
            for function in resource_data.get("lambda_functions", []):
                if function.get("role") == role_name:
                    blast_radius["affected_resources"].append({
                        "resource_type": "lambda_function",
                        "resource_id": function["function_name"],
                        "is_in_vpc": function.get("is_in_vpc"),
                    })
        
        # Get permissions
        blast_radius["permissions"] = identity.get("attached_policies", [])
        
        # Calculate risk score
        resource_count = len(blast_radius["affected_resources"])
        policy_count = len(blast_radius["permissions"])
        public_resources = sum(1 for r in blast_radius["affected_resources"] if r.get("is_public"))
        
        blast_radius["risk_score"] = min(100, (resource_count * 10) + (policy_count * 5) + (public_resources * 20))
        
        logger.info(f"Blast radius calculated: {resource_count} resources, risk score {blast_radius['risk_score']}")
        return blast_radius
