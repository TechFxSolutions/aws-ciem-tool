"""
Relationships API Routes
Provides graph data and relationship mappings
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from ...utils import app_logger as logger
from .scan import scan_results

router = APIRouter(prefix="/api/v1/relationships", tags=["Relationships"])


@router.get("/graph")
async def get_graph_data(
    scan_id: str,
    include_orphaned: bool = Query(False, description="Include resources without IAM roles")
):
    """
    Get graph data for visualization
    
    Args:
        scan_id: Scan identifier
        include_orphaned: Include resources without IAM roles
    
    Returns:
        Graph data with nodes and edges
    """
    try:
        if scan_id not in scan_results:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        scan_data = scan_results[scan_id]
        relationships = scan_data.get("relationships", {})
        graph_data = relationships.get("graph_data", {})
        
        if not include_orphaned:
            # Filter out orphaned resources
            # (This is a simplified version - you can enhance based on needs)
            pass
        
        return graph_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get graph data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/consolidated")
async def get_consolidated_view(scan_id: str):
    """
    Get consolidated hierarchical view (Level 1)
    All resources grouped by IAM role
    
    Args:
        scan_id: Scan identifier
    
    Returns:
        Consolidated view with IAM roles and their resources
    """
    try:
        if scan_id not in scan_results:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        scan_data = scan_results[scan_id]
        relationships = scan_data.get("relationships", {})
        consolidated = relationships.get("consolidated_view", {})
        
        return consolidated
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get consolidated view: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/role/{role_name}")
async def get_role_relationships(role_name: str, scan_id: str):
    """
    Get all relationships for a specific IAM role (Level 4)
    
    Args:
        role_name: IAM role name
        scan_id: Scan identifier
    
    Returns:
        Role details with resources and security groups
    """
    try:
        if scan_id not in scan_results:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        scan_data = scan_results[scan_id]
        relationships = scan_data.get("relationships", {})
        role_mappings = relationships.get("role_mappings", {})
        
        if role_name not in role_mappings:
            raise HTTPException(status_code=404, detail="Role not found")
        
        role_data = role_mappings[role_name]
        
        # Enrich with security group details
        sg_mappings = relationships.get("security_group_mappings", {})
        enriched_sgs = []
        
        for sg_id in role_data.get("security_groups", []):
            if sg_id in sg_mappings:
                enriched_sgs.append(sg_mappings[sg_id])
        
        role_data["security_group_details"] = enriched_sgs
        
        return role_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get role relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security-group/{group_id}")
async def get_security_group_relationships(group_id: str, scan_id: str):
    """
    Get all relationships for a specific security group (Level 5)
    
    Args:
        group_id: Security group ID
        scan_id: Scan identifier
    
    Returns:
        Security group details with connected resources
    """
    try:
        if scan_id not in scan_results:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        scan_data = scan_results[scan_id]
        relationships = scan_data.get("relationships", {})
        sg_mappings = relationships.get("security_group_mappings", {})
        
        if group_id not in sg_mappings:
            raise HTTPException(status_code=404, detail="Security group not found")
        
        return sg_mappings[group_id]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get security group relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resource/{resource_id}")
async def get_resource_relationships(resource_id: str, scan_id: str):
    """
    Get all relationships for a specific resource
    
    Args:
        resource_id: Resource identifier
        scan_id: Scan identifier
    
    Returns:
        Resource relationships (IAM role, security groups, etc.)
    """
    try:
        if scan_id not in scan_results:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        scan_data = scan_results[scan_id]
        relationships = scan_data.get("relationships", {})
        
        # Search for the resource
        role_mappings = relationships.get("role_mappings", {})
        sg_mappings = relationships.get("security_group_mappings", {})
        
        resource_info = {
            "resource_id": resource_id,
            "iam_roles": [],
            "security_groups": [],
            "resource_details": None,
        }
        
        # Find in role mappings
        for role_name, role_data in role_mappings.items():
            for resource in role_data.get("resources", []):
                if resource.get("resource_id") == resource_id:
                    resource_info["iam_roles"].append({
                        "role_name": role_name,
                        "role_arn": role_data.get("role_arn"),
                        "role_type": role_data.get("role_type"),
                    })
                    resource_info["resource_details"] = resource
        
        # Find in security group mappings
        for sg_id, sg_data in sg_mappings.items():
            for resource in sg_data.get("resources", []):
                if resource.get("resource_id") == resource_id:
                    resource_info["security_groups"].append({
                        "group_id": sg_id,
                        "group_name": sg_data.get("group_name"),
                        "has_internet_access": sg_data.get("has_internet_access"),
                    })
        
        if not resource_info["resource_details"]:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        return resource_info
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get resource relationships: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/internet-exposed")
async def get_internet_exposed_resources(scan_id: str):
    """
    Get all resources exposed to the Internet (Level 2.2)
    
    Args:
        scan_id: Scan identifier
    
    Returns:
        List of Internet-exposed resources with their paths
    """
    try:
        if scan_id not in scan_results:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        scan_data = scan_results[scan_id]
        relationships = scan_data.get("relationships", {})
        sg_mappings = relationships.get("security_group_mappings", {})
        
        exposed_resources = []
        
        # Find security groups with Internet access
        for sg_id, sg_data in sg_mappings.items():
            if sg_data.get("has_internet_access"):
                for resource in sg_data.get("resources", []):
                    exposed_resources.append({
                        "resource_id": resource.get("resource_id"),
                        "resource_name": resource.get("resource_name"),
                        "resource_type": resource.get("resource_type"),
                        "security_group_id": sg_id,
                        "security_group_name": sg_data.get("group_name"),
                        "risky_rules": sg_data.get("risky_rules", []),
                        "iam_role": resource.get("iam_role"),
                    })
        
        return {
            "total_exposed": len(exposed_resources),
            "resources": exposed_resources
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Internet-exposed resources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/access-path")
async def get_access_path(
    source: str,
    target: str,
    scan_id: str
):
    """
    Get access path between two entities
    
    Args:
        source: Source entity (IAM role, resource, etc.)
        target: Target entity
        scan_id: Scan identifier
    
    Returns:
        Access path with intermediate nodes
    """
    try:
        if scan_id not in scan_results:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        scan_data = scan_results[scan_id]
        relationships = scan_data.get("relationships", {})
        graph_data = relationships.get("graph_data", {})
        
        # Simple path finding (can be enhanced with graph algorithms)
        nodes = {node["id"]: node for node in graph_data.get("nodes", [])}
        edges = graph_data.get("edges", [])
        
        # Build adjacency list
        adjacency = {}
        for edge in edges:
            src = edge["source"]
            tgt = edge["target"]
            if src not in adjacency:
                adjacency[src] = []
            adjacency[src].append({"target": tgt, "type": edge["type"]})
        
        # BFS to find path
        from collections import deque
        
        queue = deque([(source, [source])])
        visited = {source}
        
        while queue:
            current, path = queue.popleft()
            
            if current == target:
                # Found path
                path_details = []
                for i, node_id in enumerate(path):
                    node_info = nodes.get(node_id, {"id": node_id, "label": node_id})
                    path_details.append(node_info)
                    
                    if i < len(path) - 1:
                        # Find edge type
                        next_node = path[i + 1]
                        edge_type = next((
                            e["type"] for e in edges
                            if e["source"] == node_id and e["target"] == next_node
                        ), "connected_to")
                        path_details[-1]["edge_to_next"] = edge_type
                
                return {
                    "source": source,
                    "target": target,
                    "path_length": len(path) - 1,
                    "path": path_details
                }
            
            # Explore neighbors
            for neighbor in adjacency.get(current, []):
                neighbor_id = neighbor["target"]
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))
        
        # No path found
        return {
            "source": source,
            "target": target,
            "path_found": False,
            "message": "No path found between source and target"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get access path: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_relationships_summary(scan_id: str):
    """
    Get summary of relationships
    
    Args:
        scan_id: Scan identifier
    
    Returns:
        Relationship statistics
    """
    try:
        if scan_id not in scan_results:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        scan_data = scan_results[scan_id]
        relationships = scan_data.get("relationships", {})
        
        return relationships.get("summary", {})
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get relationships summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
