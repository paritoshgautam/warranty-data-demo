"""
Pydantic Models - Request/Response schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class WarrantyRecord(BaseModel):
    """Single warranty record"""
    issue_number: Optional[str] = None
    assignment_status: str
    resolution_status: str
    model: str
    model_year: Any
    ecu: str
    cluster: str
    
    class Config:
        from_attributes = True

class WarrantyResponse(BaseModel):
    """Response with warranty data"""
    total: int = Field(description="Total records in database")
    count: int = Field(description="Records in this response")
    data: List[Dict[str, Any]]

class FilterRequest(BaseModel):
    """Request to filter warranty data"""
    filters: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "filters": {
                    "assignment_status": "Assigned",
                    "resolution_status": "Resolved"
                }
            }
        }

class StatsResponse(BaseModel):
    """Statistics response"""
    total_issues: int
    assigned: int
    unassigned: int
    resolved: int
    unresolved: int
    unique_models: int
    unique_years: int
    unique_ecus: int
    unique_clusters: int
