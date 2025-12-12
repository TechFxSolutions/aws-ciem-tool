"""
Relationship Builder Module
Maps relationships between IAM identities, resources, and security groups
Implements the hierarchical structure from the CIEM diagram
"""
from typing import Dict, List, Any, Set
from ..utils import app_logger as logger


class RelationshipBuilder:
    """Builds and analyzes relationships between AWS resources"""
    
    def __init__(self):
        self.relationships = []
        self.graph_data = {
            "nodes": [],
            "edges": []
        }
    
    def build_relationships(self, iam_data: Dict, resource_data: Dict) -> Dict[str, Any]:
        """
        Build complete relationship map
        
        Implements the hierarchical structure:
        Level 1: IAM Roles (consolidated view)
        Level 2: Resources grouped by Security Group
        Level 3: Security Groups
        Level 4: Individual IAM Roles
        Level 5: Resources in Security Groups
        
        Args:
            iam_data: IAM discovery results
            resource_data: Resource discovery results
        
        Returns:
            Dictionary containing relationship mappings
        """
        logger.info("Building resource relationships")
        
        # Build role-to-resource mappings
        role_mappings = self._build_role_resource_map(iam_data, resource_data)
        
        # Build security group mappings
        sg_mappings = self._build_security_group_map(resource_data)
        
        # Build consolidated view (Level 1)
        consolidated_view = self._build_consolidated_view(role_mappings, sg_mappings)
        
        # Build graph data for visualization
        graph_data = self._build_graph_data(role_mappings, sg_mappings, resource_data)
        
        result = {
            "role_mappings": role_mappings,
            "security_group_mappings": sg_mappings,
            "consolidated_view": consolidated_view,
            "graph_data": graph_data,
            "summary": {
                "total_roles": len(role_mappings),
                "total_security_groups": len(sg_mappings),
                "total_relationships": len(self.relationships),
                "roles_with_resources": sum(1 for r in role_mappings.values() if r["resources"]),
                "security_groups_with_internet": sum(1 for sg in sg_mappings.values() if sg.get("has_internet_access")),
            }
        }
        
        logger.info(f"Relationship building completed: {result['summary']}")
        return result
    
    def _normalize_node_id(self, resource_type: str, resource_id: str) -> str:
        """
        Normalize node ID to match the format used in graph nodes
        
        Args:
            resource_type: Type of resource (e.g., 'ec2_instance', 'lambda_function')
            resource_id: Resource identifier
            
        Returns:
            Normalized node ID
        """
        # Map resource types to prefixes
        type_prefix_map = {
            "iam_role": "role",
            "iam_user": "user",
            "ec2_instance": "ec2",
            "lambda_function": "lambda",
            "s3_bucket": "s3",
            "rds_instance": "rds",
            "security_group": "sg",
        }
        
        prefix = type_prefix_map.get(resource_type, resource_type)
        return f"{prefix}-{resource_id}"
    
    def _build_role_resource_map(self, iam_data: Dict, resource_data: Dict) -> Dict[str, Any]:
        """
        Build mapping of IAM roles to resources (Level 4 → Level 3)
        
        Returns:
            Dictionary mapping role names to their resources
        """
        logger.info("Building role-to-resource mappings")
        role_map = {}
        
        # Initialize all roles
        for role in iam_data.get("roles", []):
            role_name = role["role_name"]
            role_map[role_name] = {
                "role_name": role_name,
                "role_arn": role["arn"],
                "role_type": role.get("role_type"),
                "is_admin": role.get("is_admin", False),
                "attached_policies": role.get("attached_policies", []),
                "resources": [],
                "security_groups": set(),
            }
        
        # Map EC2 instances to roles
        for instance in resource_data.get("ec2_instances", []):
            iam_profile = instance.get("iam_instance_profile")
            if iam_profile and iam_profile in role_map:
                resource_info = {
                    "resource_type": "ec2_instance",
                    "resource_id": instance["instance_id"],
                    "resource_name": instance["name"],
                    "is_public": instance.get("is_public", False),
                    "security_groups": instance.get("security_groups", []),
                }
                role_map[iam_profile]["resources"].append(resource_info)
                role_map[iam_profile]["security_groups"].update(instance.get("security_groups", []))
                
                # Create relationship
                self.relationships.append({
                    "source": iam_profile,
                    "source_type": "iam_role",
                    "target": instance["instance_id"],
                    "target_type": "ec2_instance",
                    "relationship_type": "assumes",
                })
        
        # Map Lambda functions to roles
        for function in resource_data.get("lambda_functions", []):
            role_arn = function.get("role")
            if role_arn:
                # Extract role name from ARN
                role_name = role_arn.split("/")[-1] if "/" in role_arn else role_arn
                
                if role_name in role_map:
                    resource_info = {
                        "resource_type": "lambda_function",
                        "resource_id": function["function_name"],
                        "resource_name": function["function_name"],
                        "runtime": function.get("runtime"),
                        "security_groups": function.get("security_groups", []),
                    }
                    role_map[role_name]["resources"].append(resource_info)
                    role_map[role_name]["security_groups"].update(function.get("security_groups", []))
                    
                    # Create relationship
                    self.relationships.append({
                        "source": role_name,
                        "source_type": "iam_role",
                        "target": function["function_name"],
                        "target_type": "lambda_function",
                        "relationship_type": "assumes",
                    })
        
        # Convert security_groups sets to lists
        for role_data in role_map.values():
            role_data["security_groups"] = list(role_data["security_groups"])
        
        logger.info(f"Mapped {len(role_map)} IAM roles to resources")
        return role_map
    
    def _build_security_group_map(self, resource_data: Dict) -> Dict[str, Any]:
        """
        Build mapping of security groups to resources (Level 3 → Level 5)
        
        Returns:
            Dictionary mapping security group IDs to their resources
        """
        logger.info("Building security group mappings")
        sg_map = {}
        
        # Initialize from security_groups data
        for sg in resource_data.get("security_groups", []):
            sg_id = sg["group_id"]
            sg_map[sg_id] = {
                "group_id": sg_id,
                "group_name": sg["group_name"],
                "vpc_id": sg.get("vpc_id"),
                "has_internet_access": sg.get("has_internet_access", False),
                "allows_all_traffic": sg.get("allows_all_traffic", False),
                "resources": [],
            }
        
        # Map EC2 instances to security groups
        for instance in resource_data.get("ec2_instances", []):
            for sg_id in instance.get("security_groups", []):
                if sg_id not in sg_map:
                    # Create SG entry if not exists
                    sg_map[sg_id] = {
                        "group_id": sg_id,
                        "group_name": sg_id,
                        "vpc_id": None,
                        "has_internet_access": False,
                        "allows_all_traffic": False,
                        "resources": [],
                    }
                
                sg_map[sg_id]["resources"].append({
                    "resource_type": "ec2_instance",
                    "resource_id": instance["instance_id"],
                    "resource_name": instance["name"],
                    "is_public": instance.get("is_public", False),
                    "iam_role": instance.get("iam_instance_profile"),
                })
                
                # Create relationship
                self.relationships.append({
                    "source": instance["instance_id"],
                    "source_type": "ec2_instance",
                    "target": sg_id,
                    "target_type": "security_group",
                    "relationship_type": "protected_by",
                })
        
        # Map Lambda functions to security groups
        for function in resource_data.get("lambda_functions", []):
            for sg_id in function.get("security_groups", []):
                if sg_id not in sg_map:
                    sg_map[sg_id] = {
                        "group_id": sg_id,
                        "group_name": sg_id,
                        "vpc_id": None,
                        "has_internet_access": False,
                        "allows_all_traffic": False,
                        "resources": [],
                    }
                
                sg_map[sg_id]["resources"].append({
                    "resource_type": "lambda_function",
                    "resource_id": function["function_name"],
                    "resource_name": function["function_name"],
                    "iam_role": function.get("role"),
                })
                
                # Create relationship
                self.relationships.append({
                    "source": function["function_name"],
                    "source_type": "lambda_function",
                    "target": sg_id,
                    "target_type": "security_group",
                    "relationship_type": "protected_by",
                })
        
        # Map RDS instances to security groups
        for instance in resource_data.get("rds_instances", []):
            for sg_id in instance.get("security_groups", []):
                if sg_id not in sg_map:
                    sg_map[sg_id] = {
                        "group_id": sg_id,
                        "group_name": sg_id,
                        "vpc_id": None,
                        "has_internet_access": False,
                        "allows_all_traffic": False,
                        "resources": [],
                    }
                
                sg_map[sg_id]["resources"].append({
                    "resource_type": "rds_instance",
                    "resource_id": instance["db_instance_identifier"],
                    "resource_name": instance["db_instance_identifier"],
                    "publicly_accessible": instance.get("publicly_accessible", False),
                })
                
                # Create relationship
                self.relationships.append({
                    "source": instance["db_instance_identifier"],
                    "source_type": "rds_instance",
                    "target": sg_id,
                    "target_type": "security_group",
                    "relationship_type": "protected_by",
                })
        
        logger.info(f"Mapped {len(sg_map)} security groups to resources")
        return sg_map
    
    def _build_consolidated_view(self, role_mappings: Dict, sg_mappings: Dict) -> Dict[str, Any]:
        """
        Build consolidated view (Level 1) - All resources grouped by IAM role
        
        Returns:
            Hierarchical structure for UI display
        """
        logger.info("Building consolidated view")
        
        consolidated = {
            "iam_roles": [],
            "orphaned_resources": [],  # Resources without IAM roles
        }
        
        # Group by IAM role
        for role_name, role_data in role_mappings.items():
            if not role_data["resources"]:
                continue
            
            role_view = {
                "role_name": role_name,
                "role_arn": role_data["role_arn"],
                "role_type": role_data["role_type"],
                "is_admin": role_data["is_admin"],
                "resource_count": len(role_data["resources"]),
                "security_group_count": len(role_data["security_groups"]),
                "resources_by_type": {},
                "security_groups": [],
                "risk_level": self._calculate_role_risk(role_data, sg_mappings),
            }
            
            # Group resources by type
            for resource in role_data["resources"]:
                resource_type = resource["resource_type"]
                if resource_type not in role_view["resources_by_type"]:
                    role_view["resources_by_type"][resource_type] = []
                role_view["resources_by_type"][resource_type].append(resource)
            
            # Add security group details
            for sg_id in role_data["security_groups"]:
                if sg_id in sg_mappings:
                    sg_data = sg_mappings[sg_id]
                    role_view["security_groups"].append({
                        "group_id": sg_id,
                        "group_name": sg_data["group_name"],
                        "has_internet_access": sg_data["has_internet_access"],
                        "resource_count": len(sg_data["resources"]),
                    })
            
            consolidated["iam_roles"].append(role_view)
        
        # Sort by risk level
        consolidated["iam_roles"].sort(key=lambda x: x["risk_level"], reverse=True)
        
        logger.info(f"Consolidated view created with {len(consolidated['iam_roles'])} roles")
        return consolidated
    
    def _calculate_role_risk(self, role_data: Dict, sg_mappings: Dict) -> int:
        """
        Calculate risk score for a role based on its resources and permissions
        
        Returns:
            Risk score (0-100)
        """
        risk_score = 0
        
        # Admin role = high risk
        if role_data.get("is_admin"):
            risk_score += 50
        
        # Public resources = risk
        for resource in role_data["resources"]:
            if resource.get("is_public"):
                risk_score += 20
        
        # Internet-accessible security groups = risk
        for sg_id in role_data["security_groups"]:
            if sg_id in sg_mappings and sg_mappings[sg_id].get("has_internet_access"):
                risk_score += 15
        
        return min(100, risk_score)
    
    def _build_graph_data(self, role_mappings: Dict, sg_mappings: Dict, resource_data: Dict) -> Dict[str, Any]:
        """
        Build graph data for visualization (D3.js/Cytoscape.js format)
        
        Returns:
            Graph data with nodes and edges
        """
        logger.info("Building graph data for visualization")
        
        nodes = []
        edges = []
        node_ids = set()
        
        # Add IAM role nodes
        for role_name, role_data in role_mappings.items():
            if role_data["resources"]:  # Only include roles with resources
                node_id = self._normalize_node_id("iam_role", role_name)
                if node_id not in node_ids:
                    nodes.append({
                        "id": node_id,
                        "label": role_name,
                        "type": "iam_role",
                        "group": "identity",
                        "is_admin": role_data.get("is_admin", False),
                        "resource_count": len(role_data["resources"]),
                    })
                    node_ids.add(node_id)
        
        # Add security group nodes
        for sg_id, sg_data in sg_mappings.items():
            if sg_data["resources"]:  # Only include SGs with resources
                node_id = self._normalize_node_id("security_group", sg_id)
                if node_id not in node_ids:
                    nodes.append({
                        "id": node_id,
                        "label": sg_data["group_name"],
                        "type": "security_group",
                        "group": "network",
                        "has_internet_access": sg_data.get("has_internet_access", False),
                        "resource_count": len(sg_data["resources"]),
                    })
                    node_ids.add(node_id)
        
        # Add resource nodes
        for instance in resource_data.get("ec2_instances", []):
            node_id = self._normalize_node_id("ec2_instance", instance['instance_id'])
            if node_id not in node_ids:
                nodes.append({
                    "id": node_id,
                    "label": instance["name"],
                    "type": "ec2_instance",
                    "group": "compute",
                    "is_public": instance.get("is_public", False),
                    "state": instance.get("state"),
                })
                node_ids.add(node_id)
        
        for function in resource_data.get("lambda_functions", []):
            node_id = self._normalize_node_id("lambda_function", function['function_name'])
            if node_id not in node_ids:
                nodes.append({
                    "id": node_id,
                    "label": function["function_name"],
                    "type": "lambda_function",
                    "group": "compute",
                    "runtime": function.get("runtime"),
                })
                node_ids.add(node_id)
        
        for bucket in resource_data.get("s3_buckets", []):
            node_id = self._normalize_node_id("s3_bucket", bucket['bucket_name'])
            if node_id not in node_ids:
                nodes.append({
                    "id": node_id,
                    "label": bucket["bucket_name"],
                    "type": "s3_bucket",
                    "group": "storage",
                    "is_public": bucket.get("is_public", False),
                })
                node_ids.add(node_id)
        
        for instance in resource_data.get("rds_instances", []):
            node_id = self._normalize_node_id("rds_instance", instance['db_instance_identifier'])
            if node_id not in node_ids:
                nodes.append({
                    "id": node_id,
                    "label": instance["db_instance_identifier"],
                    "type": "rds_instance",
                    "group": "database",
                    "publicly_accessible": instance.get("publicly_accessible", False),
                })
                node_ids.add(node_id)
        
        # Add Internet node for visualization
        internet_node_id = "internet"
        nodes.append({
            "id": internet_node_id,
            "label": "Internet (0.0.0.0/0)",
            "type": "internet",
            "group": "external",
        })
        node_ids.add(internet_node_id)
        
        # Add edges from relationships with normalized IDs
        for rel in self.relationships:
            source_id = self._normalize_node_id(rel['source_type'], rel['source'])
            target_id = self._normalize_node_id(rel['target_type'], rel['target'])
            
            # Only add edge if both nodes exist
            if source_id in node_ids and target_id in node_ids:
                edges.append({
                    "source": source_id,
                    "target": target_id,
                    "type": rel["relationship_type"],
                })
        
        # Add edges from security groups to Internet
        for sg_id, sg_data in sg_mappings.items():
            if sg_data.get("has_internet_access"):
                source_id = self._normalize_node_id("security_group", sg_id)
                if source_id in node_ids:
                    edges.append({
                        "source": source_id,
                        "target": internet_node_id,
                        "type": "allows_traffic_from",
                    })
        
        graph_data = {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": {
                    "iam_roles": sum(1 for n in nodes if n["type"] == "iam_role"),
                    "security_groups": sum(1 for n in nodes if n["type"] == "security_group"),
                    "ec2_instances": sum(1 for n in nodes if n["type"] == "ec2_instance"),
                    "lambda_functions": sum(1 for n in nodes if n["type"] == "lambda_function"),
                    "s3_buckets": sum(1 for n in nodes if n["type"] == "s3_bucket"),
                    "rds_instances": sum(1 for n in nodes if n["type"] == "rds_instance"),
                }
            }
        }
        
        logger.info(f"Graph data created: {graph_data['stats']}")
        return graph_data
