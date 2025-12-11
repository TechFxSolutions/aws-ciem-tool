"""
AWS Resource Discovery Module
Discovers EC2, Lambda, S3, RDS, and other AWS resources
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from botocore.exceptions import ClientError
from ..utils import aws_client_manager, app_logger as logger


class ResourceDiscoverer:
    """Discovers AWS resources across services"""
    
    def __init__(self, region: str):
        self.region = region
        self.account_id = aws_client_manager.get_account_id()
    
    def discover_all(self) -> Dict[str, Any]:
        """
        Discover all resources in the region
        
        Returns:
            Dictionary containing all resource discoveries
        """
        logger.info(f"Starting resource discovery in region {self.region}")
        
        results = {
            "account_id": self.account_id,
            "region": self.region,
            "timestamp": datetime.utcnow().isoformat(),
            "ec2_instances": self.discover_ec2_instances(),
            "lambda_functions": self.discover_lambda_functions(),
            "security_groups": self.discover_security_groups(),
            "s3_buckets": self.discover_s3_buckets() if self.region == 'us-east-1' else [],
            "rds_instances": self.discover_rds_instances(),
            "summary": {}
        }
        
        # Add summary
        results["summary"] = {
            "total_ec2": len(results["ec2_instances"]),
            "total_lambda": len(results["lambda_functions"]),
            "total_security_groups": len(results["security_groups"]),
            "total_s3": len(results["s3_buckets"]),
            "total_rds": len(results["rds_instances"]),
            "public_ec2": sum(1 for i in results["ec2_instances"] if i.get("is_public")),
            "risky_security_groups": sum(1 for sg in results["security_groups"] if sg.get("has_internet_access")),
        }
        
        logger.info(f"Resource discovery completed in {self.region}: {results['summary']}")
        return results
    
    def discover_ec2_instances(self) -> List[Dict[str, Any]]:
        """Discover EC2 instances"""
        logger.info(f"Discovering EC2 instances in {self.region}")
        instances = []
        
        try:
            ec2_client = aws_client_manager.get_client('ec2', self.region)
            paginator = ec2_client.get_paginator('describe_instances')
            
            for page in paginator.paginate():
                for reservation in page['Reservations']:
                    for instance in reservation['Instances']:
                        instance_detail = self._get_ec2_details(instance)
                        instances.append(instance_detail)
            
            logger.info(f"Discovered {len(instances)} EC2 instances")
            return instances
            
        except ClientError as e:
            logger.error(f"Failed to discover EC2 instances: {str(e)}")
            return []
    
    def _get_ec2_details(self, instance: Dict) -> Dict[str, Any]:
        """Get detailed information about an EC2 instance"""
        instance_id = instance['InstanceId']
        
        # Get instance name from tags
        name = next(
            (tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'),
            instance_id
        )
        
        # Get IAM instance profile
        iam_profile = None
        if 'IamInstanceProfile' in instance:
            iam_profile = instance['IamInstanceProfile'].get('Arn', '').split('/')[-1]
        
        # Check if instance is public
        is_public = bool(instance.get('PublicIpAddress'))
        
        return {
            "instance_id": instance_id,
            "name": name,
            "instance_type": instance.get('InstanceType'),
            "state": instance['State']['Name'],
            "launch_time": instance.get('LaunchTime', '').isoformat() if instance.get('LaunchTime') else None,
            "availability_zone": instance['Placement']['AvailabilityZone'],
            "vpc_id": instance.get('VpcId'),
            "subnet_id": instance.get('SubnetId'),
            "private_ip": instance.get('PrivateIpAddress'),
            "public_ip": instance.get('PublicIpAddress'),
            "is_public": is_public,
            "security_groups": [
                {
                    "group_id": sg['GroupId'],
                    "group_name": sg['GroupName']
                }
                for sg in instance.get('SecurityGroups', [])
            ],
            "iam_instance_profile": iam_profile,
            "tags": instance.get('Tags', []),
            "platform": instance.get('Platform', 'linux'),
            "architecture": instance.get('Architecture'),
            "monitoring_state": instance.get('Monitoring', {}).get('State'),
        }
    
    def discover_lambda_functions(self) -> List[Dict[str, Any]]:
        """Discover Lambda functions"""
        logger.info(f"Discovering Lambda functions in {self.region}")
        functions = []
        
        try:
            lambda_client = aws_client_manager.get_client('lambda', self.region)
            paginator = lambda_client.get_paginator('list_functions')
            
            for page in paginator.paginate():
                for function in page['Functions']:
                    function_detail = self._get_lambda_details(function, lambda_client)
                    functions.append(function_detail)
            
            logger.info(f"Discovered {len(functions)} Lambda functions")
            return functions
            
        except ClientError as e:
            logger.error(f"Failed to discover Lambda functions: {str(e)}")
            return []
    
    def _get_lambda_details(self, function: Dict, lambda_client) -> Dict[str, Any]:
        """Get detailed information about a Lambda function"""
        function_name = function['FunctionName']
        
        # Get function configuration
        function_detail = {
            "function_name": function_name,
            "function_arn": function['FunctionArn'],
            "runtime": function.get('Runtime'),
            "role": function.get('Role', '').split('/')[-1],
            "role_arn": function.get('Role'),
            "handler": function.get('Handler'),
            "code_size": function.get('CodeSize'),
            "description": function.get('Description', ''),
            "timeout": function.get('Timeout'),
            "memory_size": function.get('MemorySize'),
            "last_modified": function.get('LastModified'),
            "version": function.get('Version'),
            "vpc_config": function.get('VpcConfig', {}),
            "environment": function.get('Environment', {}),
            "layers": function.get('Layers', []),
            "state": function.get('State'),
        }
        
        # Check if Lambda is in VPC
        vpc_config = function.get('VpcConfig', {})
        function_detail["is_in_vpc"] = bool(vpc_config.get('VpcId'))
        function_detail["security_groups"] = vpc_config.get('SecurityGroupIds', [])
        function_detail["subnets"] = vpc_config.get('SubnetIds', [])
        
        # Get tags
        try:
            tags_response = lambda_client.list_tags(Resource=function['FunctionArn'])
            function_detail["tags"] = tags_response.get('Tags', {})
        except ClientError:
            function_detail["tags"] = {}
        
        return function_detail
    
    def discover_security_groups(self) -> List[Dict[str, Any]]:
        """Discover Security Groups"""
        logger.info(f"Discovering Security Groups in {self.region}")
        security_groups = []
        
        try:
            ec2_client = aws_client_manager.get_client('ec2', self.region)
            paginator = ec2_client.get_paginator('describe_security_groups')
            
            for page in paginator.paginate():
                for sg in page['SecurityGroups']:
                    sg_detail = self._get_security_group_details(sg)
                    security_groups.append(sg_detail)
            
            logger.info(f"Discovered {len(security_groups)} Security Groups")
            return security_groups
            
        except ClientError as e:
            logger.error(f"Failed to discover Security Groups: {str(e)}")
            return []
    
    def _get_security_group_details(self, sg: Dict) -> Dict[str, Any]:
        """Get detailed information about a Security Group"""
        group_id = sg['GroupId']
        
        # Analyze ingress rules for Internet access
        has_internet_access = False
        risky_rules = []
        
        for rule in sg.get('IpPermissions', []):
            for ip_range in rule.get('IpRanges', []):
                if ip_range.get('CidrIp') == '0.0.0.0/0':
                    has_internet_access = True
                    risky_rules.append({
                        "protocol": rule.get('IpProtocol', 'all'),
                        "from_port": rule.get('FromPort'),
                        "to_port": rule.get('ToPort'),
                        "cidr": '0.0.0.0/0',
                        "description": ip_range.get('Description', '')
                    })
            
            for ipv6_range in rule.get('Ipv6Ranges', []):
                if ipv6_range.get('CidrIpv6') == '::/0':
                    has_internet_access = True
                    risky_rules.append({
                        "protocol": rule.get('IpProtocol', 'all'),
                        "from_port": rule.get('FromPort'),
                        "to_port": rule.get('ToPort'),
                        "cidr": '::/0',
                        "description": ipv6_range.get('Description', '')
                    })
        
        return {
            "group_id": group_id,
            "group_name": sg['GroupName'],
            "description": sg.get('Description', ''),
            "vpc_id": sg.get('VpcId'),
            "owner_id": sg.get('OwnerId'),
            "ingress_rules": sg.get('IpPermissions', []),
            "egress_rules": sg.get('IpPermissionsEgress', []),
            "has_internet_access": has_internet_access,
            "risky_rules": risky_rules,
            "tags": sg.get('Tags', []),
        }
    
    def discover_s3_buckets(self) -> List[Dict[str, Any]]:
        """Discover S3 buckets (only in us-east-1)"""
        logger.info("Discovering S3 buckets")
        buckets = []
        
        try:
            s3_client = aws_client_manager.get_client('s3', 'us-east-1')
            response = s3_client.list_buckets()
            
            for bucket in response.get('Buckets', []):
                bucket_detail = self._get_s3_bucket_details(bucket, s3_client)
                buckets.append(bucket_detail)
            
            logger.info(f"Discovered {len(buckets)} S3 buckets")
            return buckets
            
        except ClientError as e:
            logger.error(f"Failed to discover S3 buckets: {str(e)}")
            return []
    
    def _get_s3_bucket_details(self, bucket: Dict, s3_client) -> Dict[str, Any]:
        """Get detailed information about an S3 bucket"""
        bucket_name = bucket['Name']
        
        bucket_detail = {
            "bucket_name": bucket_name,
            "creation_date": bucket['CreationDate'].isoformat(),
        }
        
        # Get bucket location
        try:
            location = s3_client.get_bucket_location(Bucket=bucket_name)
            bucket_detail["region"] = location['LocationConstraint'] or 'us-east-1'
        except ClientError:
            bucket_detail["region"] = "unknown"
        
        # Check public access
        try:
            acl = s3_client.get_bucket_acl(Bucket=bucket_name)
            is_public = any(
                grant['Grantee'].get('URI') == 'http://acs.amazonaws.com/groups/global/AllUsers'
                for grant in acl.get('Grants', [])
            )
            bucket_detail["is_public"] = is_public
        except ClientError:
            bucket_detail["is_public"] = False
        
        # Check encryption
        try:
            encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
            bucket_detail["encryption_enabled"] = True
            bucket_detail["encryption_rules"] = encryption.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])
        except ClientError:
            bucket_detail["encryption_enabled"] = False
        
        # Check versioning
        try:
            versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
            bucket_detail["versioning_enabled"] = versioning.get('Status') == 'Enabled'
        except ClientError:
            bucket_detail["versioning_enabled"] = False
        
        return bucket_detail
    
    def discover_rds_instances(self) -> List[Dict[str, Any]]:
        """Discover RDS instances"""
        logger.info(f"Discovering RDS instances in {self.region}")
        instances = []
        
        try:
            rds_client = aws_client_manager.get_client('rds', self.region)
            paginator = rds_client.get_paginator('describe_db_instances')
            
            for page in paginator.paginate():
                for instance in page['DBInstances']:
                    instance_detail = self._get_rds_details(instance)
                    instances.append(instance_detail)
            
            logger.info(f"Discovered {len(instances)} RDS instances")
            return instances
            
        except ClientError as e:
            logger.error(f"Failed to discover RDS instances: {str(e)}")
            return []
    
    def _get_rds_details(self, instance: Dict) -> Dict[str, Any]:
        """Get detailed information about an RDS instance"""
        return {
            "db_instance_identifier": instance['DBInstanceIdentifier'],
            "db_instance_class": instance.get('DBInstanceClass'),
            "engine": instance.get('Engine'),
            "engine_version": instance.get('EngineVersion'),
            "status": instance.get('DBInstanceStatus'),
            "endpoint": instance.get('Endpoint', {}).get('Address'),
            "port": instance.get('Endpoint', {}).get('Port'),
            "availability_zone": instance.get('AvailabilityZone'),
            "multi_az": instance.get('MultiAZ', False),
            "publicly_accessible": instance.get('PubliclyAccessible', False),
            "vpc_id": instance.get('DBSubnetGroup', {}).get('VpcId'),
            "security_groups": [
                sg['VpcSecurityGroupId']
                for sg in instance.get('VpcSecurityGroups', [])
            ],
            "backup_retention_period": instance.get('BackupRetentionPeriod'),
            "encrypted": instance.get('StorageEncrypted', False),
            "iam_database_authentication": instance.get('IAMDatabaseAuthenticationEnabled', False),
            "created_time": instance.get('InstanceCreateTime', '').isoformat() if instance.get('InstanceCreateTime') else None,
        }
