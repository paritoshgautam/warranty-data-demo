"""
Analytics Routes - API endpoints for analytics and aggregations
"""
from fastapi import APIRouter, Depends
import logging

from ..services.data_service import DataService
from ..dependencies import get_data_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/stats")
async def get_statistics(
    data_service: DataService = Depends(get_data_service)
):
    """Get summary statistics"""
    try:
        return data_service.get_stats()
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise

@router.get("/sankey/{hierarchy_level}")
async def get_sankey_data(
    hierarchy_level: int,
    data_service: DataService = Depends(get_data_service)
):
    """Get data for Sankey diagram at specific hierarchy level"""
    try:
        df = data_service.get_data()
        
        hierarchies = [
            ('assignment_status', None),
            ('resolution_status', 'assignment_status'),
            ('model', 'resolution_status'),
            ('model_year', 'model'),
            ('ecu', 'model_year'),
            ('cluster', 'ecu')
        ]
        
        if hierarchy_level >= len(hierarchies):
            return {"error": "Invalid hierarchy level"}
        
        target_field, source_field = hierarchies[hierarchy_level]
        
        # Get aggregated data
        if source_field:
            flow_data = df.groupby([source_field, target_field]).size().reset_index(name='count')
            return {
                "level": hierarchy_level,
                "source_field": source_field,
                "target_field": target_field,
                "flows": flow_data.to_dict(orient='records')
            }
        else:
            counts = df[target_field].value_counts().to_dict()
            return {
                "level": hierarchy_level,
                "target_field": target_field,
                "counts": counts
            }
    except Exception as e:
        logger.error(f"Error getting Sankey data: {e}")
        raise
