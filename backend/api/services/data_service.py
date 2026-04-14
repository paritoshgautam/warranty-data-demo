"""
Data Service - Centralized data management
Handles loading, caching, and basic operations on warranty data
"""
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class DataService:
    """Singleton service for warranty data management"""
    
    def __init__(self):
        self._data: Optional[pd.DataFrame] = None
        self._cache: Dict[str, any] = {}
        
    def load_data(self) -> None:
        """Load warranty data from parquet file"""
        try:
            # Try multiple paths
            paths = [
                Path(__file__).parent.parent.parent.parent / 'data' / 'processed' / 'warranty_with_predictions.parquet',
                Path(r'c:\Users\admin\Documents\mvp-warranty-data\data\processed\warranty_with_predictions.parquet')
            ]
            
            data_path = None
            for path in paths:
                if path.exists():
                    data_path = path
                    break
            
            if not data_path:
                raise FileNotFoundError("Warranty data file not found")
            
            logger.info(f"Loading data from: {data_path}")
            df = pd.read_parquet(data_path)
            
            # Prepare data
            self._data = self._prepare_data(df)
            logger.info(f"Loaded and prepared {len(self._data)} records")
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data with derived fields"""
        df = df.copy()
        
        # Add assignment status
        if 'rca_solver_lead' in df.columns:
            df['assignment_status'] = df['rca_solver_lead'].apply(
                lambda x: 'Unassigned' if pd.isna(x) or str(x).strip() == '' else 'Assigned'
            )
        else:
            df['assignment_status'] = 'Unknown'
        
        # Add resolution status
        if 'issue_color_status' in df.columns:
            df['resolution_status'] = df['issue_color_status'].apply(
                lambda x: 'Resolved' if x in ['Dark Green', 'Cancelled'] else 'Unresolved'
            )
        else:
            df['resolution_status'] = 'Unknown'
        
        # Rename cluster column
        if 'rca_cluster_label' in df.columns:
            df['cluster'] = df['rca_cluster_label']
        
        # Fill NaN values
        df = df.fillna('Unknown')
        
        # Ensure required columns exist
        required_cols = ['assignment_status', 'resolution_status', 'model', 'model_year', 'ecu', 'cluster']
        for col in required_cols:
            if col not in df.columns:
                df[col] = 'Unknown'
        
        return df
    
    def get_data(self, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Get warranty data, optionally filtered by columns"""
        if self._data is None:
            raise ValueError("Data not loaded")
        
        if columns:
            available_cols = [col for col in columns if col in self._data.columns]
            return self._data[available_cols].copy()
        
        return self._data.copy()
    
    def get_filtered_data(self, filters: Dict[str, any]) -> pd.DataFrame:
        """Get data filtered by criteria"""
        df = self.get_data()
        
        for key, value in filters.items():
            if key in df.columns and value != 'All':
                df = df[df[key] == value]
        
        return df
    
    def get_stats(self) -> Dict[str, any]:
        """Get summary statistics"""
        cache_key = 'stats'
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        df = self.get_data()
        
        stats = {
            "total_issues": len(df),
            "assigned": int((df['assignment_status'] == 'Assigned').sum()),
            "unassigned": int((df['assignment_status'] == 'Unassigned').sum()),
            "resolved": int((df['resolution_status'] == 'Resolved').sum()),
            "unresolved": int((df['resolution_status'] == 'Unresolved').sum()),
            "unique_models": int(df['model'].nunique()),
            "unique_years": int(df['model_year'].nunique()),
            "unique_ecus": int(df['ecu'].nunique()),
            "unique_clusters": int(df['cluster'].nunique()) if 'cluster' in df.columns else 0
        }
        
        self._cache[cache_key] = stats
        return stats
    
    def get_field_values(self, field: str, limit: Optional[int] = None) -> List[str]:
        """Get unique values for a field"""
        df = self.get_data()
        
        if field not in df.columns:
            return []
        
        values = df[field].value_counts()
        if limit:
            values = values.head(limit)
        
        return values.index.tolist()
