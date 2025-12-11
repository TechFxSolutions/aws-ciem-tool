"""
AWS Client wrapper with retry logic and error handling
"""
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError
from typing import Optional, Dict, Any
from functools import lru_cache
from .config import settings
from .logger import app_logger as logger


class AWSClientManager:
    """Manages AWS client connections with retry logic"""
    
    def __init__(self):
        self.config = Config(
            retries={
                'max_attempts': 10,
                'mode': 'adaptive'
            },
            max_pool_connections=50,
            connect_timeout=10,
            read_timeout=60
        )
        self._session = None
    
    @property
    def session(self) -> boto3.Session:
        """Get or create boto3 session"""
        if self._session is None:
            if settings.aws_access_key_id and settings.aws_secret_access_key:
                self._session = boto3.Session(
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.aws_default_region
                )
            else:
                # Use default credential chain (IAM role, env vars, etc.)
                self._session = boto3.Session(region_name=settings.aws_default_region)
        return self._session
    
    @lru_cache(maxsize=128)
    def get_client(self, service_name: str, region_name: Optional[str] = None):
        """
        Get AWS service client with caching
        
        Args:
            service_name: AWS service name (e.g., 'iam', 'ec2', 'lambda')
            region_name: AWS region (defaults to configured region)
        
        Returns:
            boto3 client for the specified service
        """
        region = region_name or settings.aws_default_region
        
        try:
            client = self.session.client(
                service_name,
                region_name=region,
                config=self.config
            )
            logger.debug(f"Created {service_name} client for region {region}")
            return client
        except Exception as e:
            logger.error(f"Failed to create {service_name} client: {str(e)}")
            raise
    
    def get_account_id(self) -> str:
        """Get AWS account ID"""
        try:
            sts_client = self.get_client('sts')
            response = sts_client.get_caller_identity()
            account_id = response['Account']
            logger.info(f"Connected to AWS account: {account_id}")
            return account_id
        except ClientError as e:
            logger.error(f"Failed to get AWS account ID: {str(e)}")
            raise
    
    def get_available_regions(self, service_name: str = 'ec2') -> list:
        """
        Get list of available AWS regions for a service
        
        Args:
            service_name: AWS service name
        
        Returns:
            List of region names
        """
        try:
            ec2_client = self.get_client('ec2')
            response = ec2_client.describe_regions(AllRegions=False)
            regions = [region['RegionName'] for region in response['Regions']]
            logger.info(f"Found {len(regions)} available regions")
            return regions
        except ClientError as e:
            logger.error(f"Failed to get available regions: {str(e)}")
            return settings.aws_regions
    
    def handle_aws_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """
        Handle AWS errors and return structured error info
        
        Args:
            error: The exception that occurred
            context: Additional context about the operation
        
        Returns:
            Dictionary with error details
        """
        error_info = {
            "success": False,
            "error_type": type(error).__name__,
            "context": context
        }
        
        if isinstance(error, ClientError):
            error_code = error.response['Error']['Code']
            error_message = error.response['Error']['Message']
            error_info.update({
                "error_code": error_code,
                "error_message": error_message,
                "http_status": error.response['ResponseMetadata']['HTTPStatusCode']
            })
            
            # Log specific error types
            if error_code == 'AccessDenied':
                logger.warning(f"Access denied: {error_message} - {context}")
            elif error_code == 'ThrottlingException':
                logger.warning(f"API throttling: {error_message} - {context}")
            else:
                logger.error(f"AWS error {error_code}: {error_message} - {context}")
        
        elif isinstance(error, BotoCoreError):
            error_info["error_message"] = str(error)
            logger.error(f"Boto core error: {str(error)} - {context}")
        
        else:
            error_info["error_message"] = str(error)
            logger.error(f"Unexpected error: {str(error)} - {context}")
        
        return error_info
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test AWS connection and permissions
        
        Returns:
            Dictionary with connection test results
        """
        results = {
            "success": True,
            "account_id": None,
            "regions": [],
            "permissions": {}
        }
        
        try:
            # Test STS access
            results["account_id"] = self.get_account_id()
            
            # Test region access
            results["regions"] = self.get_available_regions()
            
            # Test IAM read access
            try:
                iam_client = self.get_client('iam')
                iam_client.list_users(MaxItems=1)
                results["permissions"]["iam"] = True
            except ClientError:
                results["permissions"]["iam"] = False
            
            # Test EC2 read access
            try:
                ec2_client = self.get_client('ec2')
                ec2_client.describe_instances(MaxResults=5)
                results["permissions"]["ec2"] = True
            except ClientError:
                results["permissions"]["ec2"] = False
            
            # Test Lambda read access
            try:
                lambda_client = self.get_client('lambda')
                lambda_client.list_functions(MaxItems=1)
                results["permissions"]["lambda"] = True
            except ClientError:
                results["permissions"]["lambda"] = False
            
            logger.info("AWS connection test completed successfully")
            
        except Exception as e:
            results["success"] = False
            results["error"] = self.handle_aws_error(e, "Connection test")
        
        return results


# Global AWS client manager instance
aws_client_manager = AWSClientManager()
