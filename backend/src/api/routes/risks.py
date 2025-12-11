"""
Risk API Routes
Provides risk analysis and assessment endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

from ...utils import app_logger as logger
from .scan import scan_results

router = APIRouter(prefix="/api/v1/risks", tags=["Risks"])


class RiskSeverity(str, Enum):
    """Risk severity levels"""
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class RiskType(str, Enum):
    """Risk types"""
    identity = "identity"
    resource = "resource"
    network = "network"
    compliance = "compliance"


@router.get("/summary")
async def get_risk_summary(scan_id: Optional[str] = None):
    """
    Get risk summary across all scans or specific scan
    
    Args:
        scan_id: Optional scan ID to filter by
    
    Returns:
        Risk summary with counts by severity
    """
    try:
        if scan_id:
            # Get risks for specific scan
            if scan_id not in scan_results:
                raise HTTPException(status_code=404, detail="Scan not found")
            
            scan_data = scan_results[scan_id]
            risk_analysis = scan_data.get("risk_analysis", {})
            
            return {
                "scan_id": scan_id,
                "summary": risk_analysis.get("risk_summary", {}),
                "top_risks": risk_analysis.get("top_risks", [])[:5],
                "timestamp": risk_analysis.get("timestamp"),
            }
        
        else:
            # Aggregate risks across all scans
            total_risks = {"critical": 0, "high": 0, "medium": 0, "low": 0, "total_risks": 0}
            all_top_risks = []
            
            for scan_id, scan_data in scan_results.items():
                risk_analysis = scan_data.get("risk_analysis", {})
                summary = risk_analysis.get("risk_summary", {})
                
                total_risks["critical"] += summary.get("critical", 0)
                total_risks["high"] += summary.get("high", 0)
                total_risks["medium"] += summary.get("medium", 0)
                total_risks["low"] += summary.get("low", 0)
                total_risks["total_risks"] += summary.get("total_risks", 0)
                
                # Collect top risks
                top_risks = risk_analysis.get("top_risks", [])
                for risk in top_risks:
                    risk["scan_id"] = scan_id
                    all_top_risks.append(risk)
            
            # Sort all top risks by score
            all_top_risks.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
            
            return {
                "summary": total_risks,
                "top_risks": all_top_risks[:10],
                "total_scans": len(scan_results),
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get risk summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_risks(
    scan_id: Optional[str] = None,
    severity: Optional[RiskSeverity] = None,
    risk_type: Optional[RiskType] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    List all risks with filtering and pagination
    
    Args:
        scan_id: Filter by scan ID
        severity: Filter by severity level
        risk_type: Filter by risk type
        limit: Maximum number of risks to return
        offset: Number of risks to skip
    
    Returns:
        Paginated list of risks
    """
    try:
        all_risks = []
        
        # Determine which scans to process
        scans_to_process = {}
        if scan_id:
            if scan_id not in scan_results:
                raise HTTPException(status_code=404, detail="Scan not found")
            scans_to_process[scan_id] = scan_results[scan_id]
        else:
            scans_to_process = scan_results
        
        # Collect all risks
        for sid, scan_data in scans_to_process.items():
            risk_analysis = scan_data.get("risk_analysis", {})
            risks_by_category = risk_analysis.get("risks", {})
            
            for category, risks in risks_by_category.items():
                for risk in risks:
                    risk["scan_id"] = sid
                    risk["category"] = category
                    all_risks.append(risk)
        
        # Apply filters
        filtered_risks = all_risks
        
        if severity:
            filtered_risks = [r for r in filtered_risks if r.get("severity") == severity.value]
        
        if risk_type:
            filtered_risks = [r for r in filtered_risks if r.get("risk_type") == risk_type.value]
        
        # Sort by risk score (highest first)
        filtered_risks.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
        
        # Apply pagination
        total = len(filtered_risks)
        paginated_risks = filtered_risks[offset:offset + limit]
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "risks": paginated_risks,
            "filters": {
                "scan_id": scan_id,
                "severity": severity.value if severity else None,
                "risk_type": risk_type.value if risk_type else None,
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list risks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{risk_id}")
async def get_risk_details(risk_id: str, scan_id: Optional[str] = None):
    """
    Get detailed information about a specific risk
    
    Args:
        risk_id: Risk identifier
        scan_id: Optional scan ID to narrow search
    
    Returns:
        Detailed risk information
    """
    try:
        # Search for the risk
        scans_to_search = {}
        if scan_id:
            if scan_id not in scan_results:
                raise HTTPException(status_code=404, detail="Scan not found")
            scans_to_search[scan_id] = scan_results[scan_id]
        else:
            scans_to_search = scan_results
        
        for sid, scan_data in scans_to_search.items():
            risk_analysis = scan_data.get("risk_analysis", {})
            risks_by_category = risk_analysis.get("risks", {})
            
            for category, risks in risks_by_category.items():
                for risk in risks:
                    if risk.get("risk_id") == risk_id:
                        risk["scan_id"] = sid
                        risk["category"] = category
                        return risk
        
        raise HTTPException(status_code=404, detail="Risk not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get risk details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blast-radius/{identity_arn:path}")
async def calculate_blast_radius(identity_arn: str, scan_id: str):
    """
    Calculate blast radius for an identity
    
    Args:
        identity_arn: ARN of the IAM identity
        scan_id: Scan ID to use for calculation
    
    Returns:
        Blast radius analysis
    """
    try:
        if scan_id not in scan_results:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        scan_data = scan_results[scan_id]
        iam_data = scan_data.get("iam_data", {})
        
        # Get combined resource data
        combined_resources = {
            "ec2_instances": [],
            "lambda_functions": [],
            "s3_buckets": [],
            "rds_instances": [],
            "security_groups": [],
        }
        
        for region, data in scan_data.get("resource_data", {}).items():
            for key in combined_resources.keys():
                if key in data:
                    combined_resources[key].extend(data[key])
        
        # Calculate blast radius
        from ...analyzers.risk_analyzer import RiskAnalyzer
        risk_analyzer = RiskAnalyzer()
        blast_radius = risk_analyzer.calculate_blast_radius(
            identity_arn,
            iam_data,
            combined_resources
        )
        
        return blast_radius
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate blast radius: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-resource/{resource_id}")
async def get_risks_by_resource(resource_id: str, scan_id: Optional[str] = None):
    """
    Get all risks associated with a specific resource
    
    Args:
        resource_id: Resource identifier
        scan_id: Optional scan ID to filter by
    
    Returns:
        List of risks for the resource
    """
    try:
        resource_risks = []
        
        scans_to_search = {}
        if scan_id:
            if scan_id not in scan_results:
                raise HTTPException(status_code=404, detail="Scan not found")
            scans_to_search[scan_id] = scan_results[scan_id]
        else:
            scans_to_search = scan_results
        
        for sid, scan_data in scans_to_search.items():
            risk_analysis = scan_data.get("risk_analysis", {})
            risks_by_category = risk_analysis.get("risks", {})
            
            for category, risks in risks_by_category.items():
                for risk in risks:
                    if risk.get("resource_id") == resource_id:
                        risk["scan_id"] = sid
                        risk["category"] = category
                        resource_risks.append(risk)
        
        # Sort by risk score
        resource_risks.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
        
        return {
            "resource_id": resource_id,
            "total_risks": len(resource_risks),
            "risks": resource_risks
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get risks by resource: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_risk_statistics(scan_id: Optional[str] = None):
    """
    Get risk statistics and trends
    
    Args:
        scan_id: Optional scan ID to filter by
    
    Returns:
        Risk statistics
    """
    try:
        stats = {
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "by_type": {"identity": 0, "resource": 0, "network": 0, "compliance": 0},
            "by_resource_type": {},
            "total_risks": 0,
        }
        
        scans_to_process = {}
        if scan_id:
            if scan_id not in scan_results:
                raise HTTPException(status_code=404, detail="Scan not found")
            scans_to_process[scan_id] = scan_results[scan_id]
        else:
            scans_to_process = scan_results
        
        for sid, scan_data in scans_to_process.items():
            risk_analysis = scan_data.get("risk_analysis", {})
            risks_by_category = risk_analysis.get("risks", {})
            
            for category, risks in risks_by_category.items():
                for risk in risks:
                    # Count by severity
                    severity = risk.get("severity", "low")
                    stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
                    
                    # Count by type
                    risk_type = risk.get("risk_type", "resource")
                    stats["by_type"][risk_type] = stats["by_type"].get(risk_type, 0) + 1
                    
                    # Count by resource type
                    resource_type = risk.get("resource_type", "unknown")
                    stats["by_resource_type"][resource_type] = stats["by_resource_type"].get(resource_type, 0) + 1
                    
                    stats["total_risks"] += 1
        
        return stats
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get risk statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
