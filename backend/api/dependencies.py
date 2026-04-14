"""
Dependency injection functions
"""
from fastapi import HTTPException

# Will be set by main.py
_data_service = None

def set_data_service(service):
    """Set the global data service instance"""
    global _data_service
    _data_service = service

def get_data_service():
    """Dependency injection for data service"""
    if _data_service is None:
        raise HTTPException(status_code=503, detail="Data service not initialized")
    return _data_service
