"""
Scan API Routes
Orchestrates discovery scans across AWS resources
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from ...discoverers.iam_discoverer import IAMDiscoverer
from ...discoverers.resource_discoverer import ResourceDiscoverer
from ...analyzers.risk_analyzer import RiskAnalyzer
from ...analyzers.relationship_builder import RelationshipBuilder
from ...utils import settings, app_logger as logger

router = APIRouter(prefix="/api/v1/scan", tags=["Scan"])

# In-memory storage for scan results (replace with database in production)
scan_results = {}
scan_status = {}


class ScanRequest(BaseModel):
    """Scan request model"""
    regions: Optional[List[str]] = None
    scan_iam: bool = True
    scan_ec2: bool = True
    scan_lambda: bool = True
    scan_s3: bool = True
    scan_rds: bool = True
    scan_security_groups: bool = True


class ScanResponse(BaseModel):
    """Scan response model"""
    scan_id: str
    status: str
    message: str
    started_at: str


def perform_scan(scan_id: str, regions: List[str], scan_config: Dict[str, bool]):
    """
    Background task to perform the scan
    
    Args:
        scan_id: Unique scan identifier
        regions: List of AWS regions to scan
        scan_config: Configuration for what to scan
    """
    try:
        logger.info(f"Starting scan {scan_id} for regions: {regions}")
        scan_status[scan_id] = {
            "status": "running",
            "progress": 0,
            "current_step": "Initializing",
            "started_at": datetime.utcnow().isoformat(),
        }
        
        all_results = {
            "scan_id": scan_id,
            "regions": regions,
            "started_at": datetime.utcnow().isoformat(),
            "iam_data": None,
            "resource_data": {},
            "risk_analysis": None,
            "relationships": None,
        }
        
        # Step 1: IAM Discovery (global)
        if scan_config.get("scan_iam", True):
            logger.info(f"[{scan_id}] Discovering IAM resources")
            scan_status[scan_id]["current_step"] = "Discovering IAM"
            scan_status[scan_id]["progress"] = 10
            
            iam_discoverer = IAMDiscoverer()
            all_results["iam_data"] = iam_discoverer.discover_all()
            logger.info(f"[{scan_id}] IAM discovery completed")
        
        # Step 2: Resource Discovery (per region)
        scan_status[scan_id]["current_step"] = "Discovering Resources"
        scan_status[scan_id]["progress"] = 30
        
        for idx, region in enumerate(regions):
            logger.info(f"[{scan_id}] Discovering resources in {region}")
            
            resource_discoverer = ResourceDiscoverer(region=region)
            region_data = {}
            
            if scan_config.get("scan_ec2", True):
                region_data["ec2_instances"] = resource_discoverer.discover_ec2_instances()
            
            if scan_config.get("scan_lambda", True):
                region_data["lambda_functions"] = resource_discoverer.discover_lambda_functions()
            
            if scan_config.get("scan_s3", True) and region == "us-east-1":
                region_data["s3_buckets"] = resource_discoverer.discover_s3_buckets()
            
            if scan_config.get("scan_rds", True):
                region_data["rds_instances"] = resource_discoverer.discover_rds_instances()
            
            if scan_config.get("scan_security_groups", True):
                region_data["security_groups"] = resource_discoverer.discover_security_groups()
            
            all_results["resource_data"][region] = region_data
            
            # Update progress
            progress = 30 + int((idx + 1) / len(regions) * 30)
            scan_status[scan_id]["progress"] = progress
            logger.info(f"[{scan_id}] Resource discovery completed for {region}")
        
        # Step 3: Risk Analysis
        logger.info(f"[{scan_id}] Analyzing risks")
        scan_status[scan_id]["current_step"] = "Analyzing Risks"
        scan_status[scan_id]["progress"] = 70
        
        risk_analyzer = RiskAnalyzer()
        
        # Combine all resource data for risk analysis
        combined_resources = {
            "ec2_instances": [],
            "lambda_functions": [],
            "s3_buckets": [],
            "rds_instances": [],
            "security_groups": [],
        }
        
        for region, data in all_results["resource_data"].items():
            for key in combined_resources.keys():
                if key in data:
                    combined_resources[key].extend(data[key])
        
        all_results["risk_analysis"] = risk_analyzer.analyze_all(
            all_results["iam_data"],
            combined_resources
        )
        logger.info(f"[{scan_id}] Risk analysis completed")
        
        # Step 4: Build Relationships
        logger.info(f"[{scan_id}] Building relationships")
        scan_status[scan_id]["current_step"] = "Building Relationships"
        scan_status[scan_id]["progress"] = 85
        
        relationship_builder = RelationshipBuilder()
        all_results["relationships"] = relationship_builder.build_relationships(
            all_results["iam_data"],
            combined_resources
        )
        logger.info(f"[{scan_id}] Relationship building completed")
        
        # Complete
        scan_status[scan_id]["status"] = "completed"
        scan_status[scan_id]["progress"] = 100
        scan_status[scan_id]["current_step"] = "Completed"
        scan_status[scan_id]["completed_at"] = datetime.utcnow().isoformat()
        
        all_results["completed_at"] = datetime.utcnow().isoformat()
        scan_results[scan_id] = all_results
        
        logger.info(f"[{scan_id}] Scan completed successfully")
        
    except Exception as e:
        logger.error(f"[{scan_id}] Scan failed: {str(e)}")
        scan_status[scan_id]["status"] = "failed"
        scan_status[scan_id]["error"] = str(e)
        scan_status[scan_id]["failed_at"] = datetime.utcnow().isoformat()


@router.post("/start", response_model=ScanResponse)
async def start_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a new discovery scan
    
    Args:
        request: Scan configuration
        background_tasks: FastAPI background tasks
    
    Returns:
        Scan ID and status
    """
    try:
        # Generate scan ID
        scan_id = str(uuid.uuid4())
        
        # Determine regions to scan
        regions = request.regions or [settings.aws_default_region]
        
        # Scan configuration
        scan_config = {
            "scan_iam": request.scan_iam,
            "scan_ec2": request.scan_ec2,
            "scan_lambda": request.scan_lambda,
            "scan_s3": request.scan_s3,
            "scan_rds": request.scan_rds,
            "scan_security_groups": request.scan_security_groups,
        }
        
        # Initialize scan status
        scan_status[scan_id] = {
            "status": "queued",
            "progress": 0,
            "current_step": "Queued",
            "started_at": datetime.utcnow().isoformat(),
        }
        
        # Start background scan
        background_tasks.add_task(perform_scan, scan_id, regions, scan_config)
        
        logger.info(f"Scan {scan_id} queued for regions: {regions}")
        
        return ScanResponse(
            scan_id=scan_id,
            status="queued",
            message="Scan started successfully",
            started_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to start scan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{scan_id}")
async def get_scan_status(scan_id: str):
    """
    Get scan status
    
    Args:
        scan_id: Scan identifier
    
    Returns:
        Scan status and progress
    """
    if scan_id not in scan_status:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return scan_status[scan_id]


@router.get("/results/{scan_id}")
async def get_scan_results(scan_id: str):
    """
    Get scan results
    
    Args:
        scan_id: Scan identifier
    
    Returns:
        Complete scan results
    """
    if scan_id not in scan_results:
        # Check if scan is still running
        if scan_id in scan_status:
            status = scan_status[scan_id]["status"]
            if status == "running" or status == "queued":
                raise HTTPException(
                    status_code=202,
                    detail=f"Scan is still {status}. Check status endpoint for progress."
                )
            elif status == "failed":
                raise HTTPException(
                    status_code=500,
                    detail=f"Scan failed: {scan_status[scan_id].get('error', 'Unknown error')}"
                )
        
        raise HTTPException(status_code=404, detail="Scan results not found")
    
    return scan_results[scan_id]


@router.get("/list")
async def list_scans(limit: int = 10, offset: int = 0):
    """
    List all scans
    
    Args:
        limit: Maximum number of scans to return
        offset: Number of scans to skip
    
    Returns:
        List of scans with status
    """
    all_scans = []
    
    for scan_id, status in scan_status.items():
        scan_info = {
            "scan_id": scan_id,
            **status
        }
        all_scans.append(scan_info)
    
    # Sort by started_at (most recent first)
    all_scans.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    
    # Apply pagination
    paginated = all_scans[offset:offset + limit]
    
    return {
        "total": len(all_scans),
        "limit": limit,
        "offset": offset,
        "scans": paginated
    }


@router.delete("/{scan_id}")
async def delete_scan(scan_id: str):
    """
    Delete scan results
    
    Args:
        scan_id: Scan identifier
    
    Returns:
        Success message
    """
    if scan_id not in scan_status:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Remove from both dictionaries
    if scan_id in scan_results:
        del scan_results[scan_id]
    
    del scan_status[scan_id]
    
    logger.info(f"Scan {scan_id} deleted")
    
    return {"message": "Scan deleted successfully", "scan_id": scan_id}
