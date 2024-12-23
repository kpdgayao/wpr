"""
Utility functions for UI operations and styling.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional

def apply_custom_css() -> None:
    """Apply custom CSS styling to the Streamlit app."""
    st.markdown("""
        <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .metric-card {
            background-color: #f8f9fa;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #1f77b4;
        }
        .metric-label {
            font-size: 1rem;
            color: #666;
        }
        </style>
    """, unsafe_allow_html=True)

def display_metric_card(label: str, value: Any, prefix: str = "", suffix: str = "") -> None:
    """
    Display a metric in a styled card format.
    
    Args:
        label (str): Metric label
        value (Any): Metric value
        prefix (str): Prefix to display before value
        suffix (str): Suffix to display after value
    """
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{prefix}{value}{suffix}</div>
            <div class="metric-label">{label}</div>
        </div>
    """, unsafe_allow_html=True)

def create_filter_section(
    data: pd.DataFrame,
    columns: List[str],
    labels: Optional[Dict[str, str]] = None
) -> Dict[str, List[Any]]:
    """
    Create a filter section with multiple select boxes.
    
    Args:
        data (pd.DataFrame): Input dataframe
        columns (List[str]): List of columns to create filters for
        labels (Optional[Dict[str, str]]): Custom labels for filters
        
    Returns:
        Dict[str, List[Any]]: Dictionary of selected values for each filter
    """
    if labels is None:
        labels = {col: f"Select {col}" for col in columns}
    
    filters = {}
    with st.sidebar:
        for col in columns:
            unique_values = sorted(data[col].unique().tolist())
            filters[col] = st.multiselect(
                labels.get(col, f"Select {col}"),
                options=unique_values
            )
    
    return filters
