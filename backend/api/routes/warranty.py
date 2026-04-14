"""
Warranty Routes - API endpoints for warranty data
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
import logging

from ..schemas import WarrantyRecord, WarrantyResponse, FilterRequest
from ..services.data_service import DataService
from ..dependencies import get_data_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/data", response_model=WarrantyResponse)
async def get_warranty_data(
    limit: Optional[int] = Query(None, description="Limit number of records"),
    offset: Optional[int] = Query(0, description="Offset for pagination"),
    data_service: DataService = Depends(get_data_service)
):
    """Get all warranty data with optional pagination"""
    try:
        df = data_service.get_data()
        
        # Apply pagination
        if limit:
            df = df.iloc[offset:offset+limit]
        
        records = df.to_dict(orient='records')
        
        return {
            "total": len(data_service.get_data()),
            "count": len(records),
            "data": records
        }
    except Exception as e:
        logger.error(f"Error fetching warranty data: {e}")
        raise

@router.post("/filter", response_model=WarrantyResponse)
async def filter_warranty_data(
    filter_request: FilterRequest,
    data_service: DataService = Depends(get_data_service)
):
    """Filter warranty data by criteria"""
    try:
        df = data_service.get_filtered_data(filter_request.filters)
        records = df.to_dict(orient='records')
        
        return {
            "total": len(data_service.get_data()),
            "count": len(records),
            "data": records
        }
    except Exception as e:
        logger.error(f"Error filtering data: {e}")
        raise

@router.get("/fields/{field}")
async def get_field_values(
    field: str,
    limit: Optional[int] = Query(20, description="Limit number of values"),
    data_service: DataService = Depends(get_data_service)
):
    """Get unique values for a specific field"""
    try:
        values = data_service.get_field_values(field, limit)
        return {
            "field": field,
            "values": values,
            "count": len(values)
        }
    except Exception as e:
        logger.error(f"Error getting field values: {e}")
        raise
