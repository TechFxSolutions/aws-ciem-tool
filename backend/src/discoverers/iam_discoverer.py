"""
IAM Identity Discovery Module
Discovers IAM Users, Roles, Groups, and Policies
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from botocore.exceptions import ClientError
from ..utils import aws_client_manager, app_logger as logger


class IAMDiscoverer:
    """Discovers and analyzes IAM identities"""
    
    def __init__(self, region: str = None):
        self.region = region
        self.iam_client = aws_client_manager.get_client('iam', region)
        self.account_id = None
    
    def discover_all(self) -> Dict[str, Any]:
        """
        Discover all IAM resources
        
        Returns:
            Dictionary containing all IAM discoveries
        """
        logger.info("Starting IAM discovery")
        
        try:
            self.account_id = aws_client_manager.get_account_id()
            
            results = {
                "account_id": self.account_id,
                "timestamp": datetime.utcnow().isoformat(),
                "users": self.discover_users(),
                "roles": self.discover_roles(),
                "groups": self.discover_groups(),
                "policies": self.discover_policies(),
                "summary": {}
            }
            
            # Add summary statistics
            results["summary"] = {
                "total_users": len(results["users"]),
                "total_roles": len(results["roles"]),
                "total_groups": len(results["groups"]),
                "total_policies": len(results["policies"]),
                "users_with_mfa": sum(1 for u in results["users"] if u.get("mfa_enabled")),
                "users_without_mfa": sum(1 for u in results["users"] if not u.get("mfa_enabled")),
                "inactive_users": sum(1 for u in results["users"] if u.get("is_inactive")),
                "admin_roles": sum(1 for r in results["roles"] if r.get("is_admin")),
            }
            
            logger.info(f"IAM discovery completed: {results['summary']}")
            return results
            
        except Exception as e:
            logger.error(f"IAM discovery failed: {str(e)}")
            raise
    
    def discover_users(self) -> List[Dict[str, Any]]:
        """
        Discover all IAM users
        
        Returns:
            List of IAM user details
        """
        logger.info("Discovering IAM users")
        users = []
        
        try:
            paginator = self.iam_client.get_paginator('list_users')
            
            for page in paginator.paginate():
                for user in page['Users']:
                    user_detail = self._get_user_details(user)
                    users.append(user_detail)
            
            logger.info(f"Discovered {len(users)} IAM users")
            return users
            
        except ClientError as e:
            logger.error(f"Failed to discover IAM users: {str(e)}")
            return []
    
    def _get_user_details(self, user: Dict) -> Dict[str, Any]:
        """Get detailed information about an IAM user"""
        username = user['UserName']
        
        try:
            # Get user details
            user_detail = {
                "username": username,
                "user_id": user['UserId'],
                "arn": user['Arn'],
                "created_date": user['CreateDate'].isoformat(),
                "path": user.get('Path', '/'),
                "tags": user.get('Tags', []),
            }
            
            # Check MFA status
            try:
                mfa_devices = self.iam_client.list_mfa_devices(UserName=username)
                user_detail["mfa_enabled"] = len(mfa_devices['MFADevices']) > 0
                user_detail["mfa_devices"] = mfa_devices['MFADevices']
            except ClientError:
                user_detail["mfa_enabled"] = False
                user_detail["mfa_devices"] = []
            
            # Get access keys
            try:
                access_keys = self.iam_client.list_access_keys(UserName=username)
                user_detail["access_keys"] = [
                    {
                        "access_key_id": key['AccessKeyId'],
                        "status": key['Status'],
                        "created_date": key['CreateDate'].isoformat()
                    }
                    for key in access_keys['AccessKeyMetadata']
                ]
            except ClientError:
                user_detail["access_keys"] = []
            
            # Get attached policies
            try:
                attached_policies = self.iam_client.list_attached_user_policies(UserName=username)
                user_detail["attached_policies"] = [
                    {
                        "policy_name": policy['PolicyName'],
                        "policy_arn": policy['PolicyArn']
                    }
                    for policy in attached_policies['AttachedPolicies']
                ]
            except ClientError:
                user_detail["attached_policies"] = []
            
            # Get inline policies
            try:
                inline_policies = self.iam_client.list_user_policies(UserName=username)
                user_detail["inline_policies"] = inline_policies['PolicyNames']
            except ClientError:
                user_detail["inline_policies"] = []
            
            # Get groups
            try:
                groups = self.iam_client.list_groups_for_user(UserName=username)
                user_detail["groups"] = [group['GroupName'] for group in groups['Groups']]
            except ClientError:
                user_detail["groups"] = []
            
            # Check if user is inactive (no activity in last 90 days)
            try:
                last_used = self.iam_client.get_user(UserName=username)
                password_last_used = last_used['User'].get('PasswordLastUsed')
                if password_last_used:
                    days_since_login = (datetime.now(password_last_used.tzinfo) - password_last_used).days
                    user_detail["days_since_login"] = days_since_login
                    user_detail["is_inactive"] = days_since_login > 90
                else:
                    user_detail["days_since_login"] = None
                    user_detail["is_inactive"] = True
            except ClientError:
                user_detail["is_inactive"] = False
            
            return user_detail
            
        except Exception as e:
            logger.error(f"Failed to get details for user {username}: {str(e)}")
            return {
                "username": username,
                "error": str(e)
            }
    
    def discover_roles(self) -> List[Dict[str, Any]]:
        """
        Discover all IAM roles
        
        Returns:
            List of IAM role details
        """
        logger.info("Discovering IAM roles")
        roles = []
        
        try:
            paginator = self.iam_client.get_paginator('list_roles')
            
            for page in paginator.paginate():
                for role in page['Roles']:
                    role_detail = self._get_role_details(role)
                    roles.append(role_detail)
            
            logger.info(f"Discovered {len(roles)} IAM roles")
            return roles
            
        except ClientError as e:
            logger.error(f"Failed to discover IAM roles: {str(e)}")
            return []
    
    def _get_role_details(self, role: Dict) -> Dict[str, Any]:
        """Get detailed information about an IAM role"""
        role_name = role['RoleName']
        
        try:
            role_detail = {
                "role_name": role_name,
                "role_id": role['RoleId'],
                "arn": role['Arn'],
                "created_date": role['CreateDate'].isoformat(),
                "path": role.get('Path', '/'),
                "assume_role_policy": role.get('AssumeRolePolicyDocument', {}),
                "description": role.get('Description', ''),
                "max_session_duration": role.get('MaxSessionDuration', 3600),
                "tags": role.get('Tags', []),
            }
            
            # Get attached policies
            try:
                attached_policies = self.iam_client.list_attached_role_policies(RoleName=role_name)
                role_detail["attached_policies"] = [
                    {
                        "policy_name": policy['PolicyName'],
                        "policy_arn": policy['PolicyArn']
                    }
                    for policy in attached_policies['AttachedPolicies']
                ]
                
                # Check if role has admin access
                role_detail["is_admin"] = any(
                    'AdministratorAccess' in policy['PolicyName'] or
                    'FullAccess' in policy['PolicyName']
                    for policy in attached_policies['AttachedPolicies']
                )
            except ClientError:
                role_detail["attached_policies"] = []
                role_detail["is_admin"] = False
            
            # Get inline policies
            try:
                inline_policies = self.iam_client.list_role_policies(RoleName=role_name)
                role_detail["inline_policies"] = inline_policies['PolicyNames']
            except ClientError:
                role_detail["inline_policies"] = []
            
            # Determine role type (service role, cross-account, etc.)
            assume_policy = role.get('AssumeRolePolicyDocument', {})
            role_detail["role_type"] = self._determine_role_type(assume_policy)
            
            return role_detail
            
        except Exception as e:
            logger.error(f"Failed to get details for role {role_name}: {str(e)}")
            return {
                "role_name": role_name,
                "error": str(e)
            }
    
    def _determine_role_type(self, assume_policy: Dict) -> str:
        """Determine the type of IAM role based on trust policy"""
        if not assume_policy or 'Statement' not in assume_policy:
            return "unknown"
        
        for statement in assume_policy['Statement']:
            principal = statement.get('Principal', {})
            
            if isinstance(principal, dict):
                if 'Service' in principal:
                    services = principal['Service']
                    if isinstance(services, str):
                        services = [services]
                    
                    if any('ec2.amazonaws.com' in s for s in services):
                        return "ec2_instance_role"
                    elif any('lambda.amazonaws.com' in s for s in services):
                        return "lambda_execution_role"
                    elif any('ecs-tasks.amazonaws.com' in s for s in services):
                        return "ecs_task_role"
                    else:
                        return "service_role"
                
                elif 'AWS' in principal:
                    return "cross_account_role"
                
                elif 'Federated' in principal:
                    return "federated_role"
        
        return "unknown"
    
    def discover_groups(self) -> List[Dict[str, Any]]:
        """
        Discover all IAM groups
        
        Returns:
            List of IAM group details
        """
        logger.info("Discovering IAM groups")
        groups = []
        
        try:
            paginator = self.iam_client.get_paginator('list_groups')
            
            for page in paginator.paginate():
                for group in page['Groups']:
                    group_detail = self._get_group_details(group)
                    groups.append(group_detail)
            
            logger.info(f"Discovered {len(groups)} IAM groups")
            return groups
            
        except ClientError as e:
            logger.error(f"Failed to discover IAM groups: {str(e)}")
            return []
    
    def _get_group_details(self, group: Dict) -> Dict[str, Any]:
        """Get detailed information about an IAM group"""
        group_name = group['GroupName']
        
        try:
            group_detail = {
                "group_name": group_name,
                "group_id": group['GroupId'],
                "arn": group['Arn'],
                "created_date": group['CreateDate'].isoformat(),
                "path": group.get('Path', '/'),
            }
            
            # Get group members
            try:
                members = self.iam_client.get_group(GroupName=group_name)
                group_detail["members"] = [user['UserName'] for user in members['Users']]
                group_detail["member_count"] = len(members['Users'])
            except ClientError:
                group_detail["members"] = []
                group_detail["member_count"] = 0
            
            # Get attached policies
            try:
                attached_policies = self.iam_client.list_attached_group_policies(GroupName=group_name)
                group_detail["attached_policies"] = [
                    {
                        "policy_name": policy['PolicyName'],
                        "policy_arn": policy['PolicyArn']
                    }
                    for policy in attached_policies['AttachedPolicies']
                ]
            except ClientError:
                group_detail["attached_policies"] = []
            
            # Get inline policies
            try:
                inline_policies = self.iam_client.list_group_policies(GroupName=group_name)
                group_detail["inline_policies"] = inline_policies['PolicyNames']
            except ClientError:
                group_detail["inline_policies"] = []
            
            return group_detail
            
        except Exception as e:
            logger.error(f"Failed to get details for group {group_name}: {str(e)}")
            return {
                "group_name": group_name,
                "error": str(e)
            }
    
    def discover_policies(self, scope: str = 'Local') -> List[Dict[str, Any]]:
        """
        Discover IAM policies
        
        Args:
            scope: 'Local' for customer managed, 'AWS' for AWS managed, 'All' for both
        
        Returns:
            List of IAM policy details
        """
        logger.info(f"Discovering IAM policies (scope: {scope})")
        policies = []
        
        try:
            paginator = self.iam_client.get_paginator('list_policies')
            
            for page in paginator.paginate(Scope=scope):
                for policy in page['Policies']:
                    policy_detail = {
                        "policy_name": policy['PolicyName'],
                        "policy_id": policy['PolicyId'],
                        "arn": policy['Arn'],
                        "path": policy.get('Path', '/'),
                        "default_version_id": policy.get('DefaultVersionId'),
                        "attachment_count": policy.get('AttachmentCount', 0),
                        "permissions_boundary_usage_count": policy.get('PermissionsBoundaryUsageCount', 0),
                        "is_attachable": policy.get('IsAttachable', False),
                        "description": policy.get('Description', ''),
                        "created_date": policy['CreateDate'].isoformat(),
                        "updated_date": policy.get('UpdateDate', policy['CreateDate']).isoformat(),
                    }
                    policies.append(policy_detail)
            
            logger.info(f"Discovered {len(policies)} IAM policies")
            return policies
            
        except ClientError as e:
            logger.error(f"Failed to discover IAM policies: {str(e)}")
            return []
