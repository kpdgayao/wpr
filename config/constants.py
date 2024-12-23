"""
Constants used throughout the WPR application.
"""

class Constants:
    """Application-wide constants."""
    
    # AI Configuration
    MAX_TOKENS = 4000
    AI_MODEL = "claude-3-5-sonnet-20241022"
    
    # Logging
    LOG_FILE = "wpr.log"
    
    # UI Configuration
    PAGE_TITLE = "IOL Weekly Productivity Report"
    PAGE_ICON = ":clipboard:"
    
    # Cache Configuration
    CACHE_TTL = 3600  # 1 hour in seconds
