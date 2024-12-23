"""
Utility functions for data processing and validation.
"""
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime, timedelta

def validate_numeric_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Validate and convert numeric columns in a dataframe.
    
    Args:
        df (pd.DataFrame): Input dataframe
        columns (List[str]): List of column names to validate
        
    Returns:
        pd.DataFrame: DataFrame with validated numeric columns
    """
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def format_timestamp(timestamp: datetime) -> str:
    """
    Format timestamp in a consistent way.
    
    Args:
        timestamp (datetime): Input timestamp
        
    Returns:
        str: Formatted timestamp string
    """
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def calculate_week_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate weekly statistics from dataframe.
    
    Args:
        df (pd.DataFrame): Input dataframe with weekly data
        
    Returns:
        Dict[str, Any]: Dictionary containing weekly statistics
    """
    stats = {
        'total_completed': df['Number of Completed Tasks'].sum(),
        'total_pending': df['Number of Pending Tasks'].sum(),
        'total_dropped': df['Number of Dropped Tasks'].sum(),
        'avg_productivity': df['Productivity Rating'].mean(),
        'week_numbers': sorted(df['Week Number'].unique().tolist())
    }
    return stats

def safe_get_nested(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    Safely get nested dictionary values.
    
    Args:
        data (Dict[str, Any]): Input dictionary
        keys (List[str]): List of keys to traverse
        default (Any): Default value if key not found
        
    Returns:
        Any: Value at nested key location or default
    """
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return default
    return data
