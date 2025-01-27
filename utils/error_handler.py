"""Error handling utilities for the WPR application."""

import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, Union
import streamlit as st

def handle_exceptions(
    error_types: Union[Type[Exception], tuple] = Exception,
    display_error: bool = True,
    log_error: bool = True,
    default_return: Any = None
) -> Callable:
    """
    Decorator for handling exceptions in a consistent way across the application.
    
    Args:
        error_types: Exception type or tuple of exception types to catch
        display_error: Whether to display error to user via Streamlit
        log_error: Whether to log the error
        default_return: Value to return if an exception occurs
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except error_types as e:
                if log_error:
                    logging.error(f"Error in {func.__name__}: {str(e)}")
                if display_error:
                    st.error(f"An error occurred: {str(e)}")
                return default_return
        return wrapper
    return decorator

def format_error_message(
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format error message with optional context for consistent error reporting.
    
    Args:
        error: The exception that occurred
        context: Optional dictionary of contextual information
        
    Returns:
        Formatted error message string
    """
    message = f"Error: {str(error)}"
    if context:
        message += "\nContext:\n"
        for key, value in context.items():
            message += f"  {key}: {value}\n"
    return message
