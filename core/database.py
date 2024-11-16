# core/database.py
import logging
from supabase import create_client
import pandas as pd
from datetime import datetime
import streamlit as st

class DatabaseHandler:
    def __init__(self, supabase_url, supabase_key):
        """Initialize database connection"""
        try:
            self.client = create_client(supabase_url, supabase_key)
            self.table_name = 'wpr_reports'
            logging.info("Database connection initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize database connection: {str(e)}")
            raise

    def save_data(self, data):
        """Save WPR data to database"""
        try:
            # Add timestamp to data
            data['timestamp'] = datetime.now().isoformat()
            
            # Insert data into Supabase
            result = self.client.table(self.table_name).insert(data).execute()
            logging.info(f"Data saved successfully: {result}")
            return True
        except Exception as e:
            logging.error(f"Error saving data: {str(e)}")
            return False

    def load_data(self):
        """Load all WPR data"""
        try:
            result = self.client.table(self.table_name).select("*").execute()
            return pd.DataFrame(result.data)
        except Exception as e:
            logging.error(f"Error loading data: {str(e)}")
            return pd.DataFrame()

    def get_user_reports(self, user_name, limit=5):
        """Get recent reports for a specific user"""
        try:
            result = self.client.table(self.table_name)\
                .select("*")\
                .eq("Name", user_name)\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            return pd.DataFrame(result.data)
        except Exception as e:
            logging.error(f"Error getting user reports: {str(e)}")
            return pd.DataFrame()

    def check_existing_submission(self, name, week_number, year):
        """Check if user has already submitted for the given week"""
        try:
            result = self.client.table(self.table_name)\
                .select("*")\
                .eq("Name", name)\
                .eq("Week Number", week_number)\
                .eq("Year", year)\
                .execute()
            return len(result.data) > 0
        except Exception as e:
            logging.error(f"Error checking existing submission: {str(e)}")
            return False

    def get_team_reports(self, team_name, week_number=None):
        """Get reports for an entire team"""
        try:
            query = self.client.table(self.table_name)\
                .select("*")\
                .eq("Team", team_name)
            
            if week_number:
                query = query.eq("Week Number", week_number)
                
            result = query.execute()
            return pd.DataFrame(result.data)
        except Exception as e:
            logging.error(f"Error getting team reports: {str(e)}")
            return pd.DataFrame()

    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_productivity_stats(self, team_name=None):
        """Get productivity statistics"""
        try:
            query = self.client.table(self.table_name).select("*")
            if team_name:
                query = query.eq("Team", team_name)
            
            result = query.execute()
            df = pd.DataFrame(result.data)
            
            if df.empty:
                return {}
                
            stats = {
                "average_productivity": df["Productivity Rating"].mean(),
                "total_reports": len(df),
                "completed_tasks": df["Number of Completed Tasks"].sum(),
                "pending_tasks": df["Number of Pending Tasks"].sum(),
                "dropped_tasks": df["Number of Dropped Tasks"].sum()
            }
            return stats
        except Exception as e:
            logging.error(f"Error getting productivity stats: {str(e)}")
            return {}
        
        # Add to your DatabaseHandler class in core/database.py
        def save_hr_analysis(self, analysis_data: Dict[str, Any]) -> bool:
            """Save HR analysis to database"""
            try:
                # Add timestamp if not present
                if 'analysis_timestamp' not in analysis_data:
                    analysis_data['analysis_timestamp'] = datetime.now().isoformat()
                
                result = self.client.table('hr_analysis').insert(analysis_data).execute()
                logging.info(f"HR analysis saved successfully: {result}")
                return True
            except Exception as e:
                logging.error(f"Error saving HR analysis: {str(e)}")
                return False

        def get_hr_analysis_history(self, employee_name: str, limit: int = 5) -> List[Dict[str, Any]]:
            """Get historical HR analysis for an employee"""
            try:
                result = self.client.table('hr_analysis')\
                    .select("*")\
                    .eq("employee_name", employee_name)\
                    .order('analysis_timestamp', desc=True)\
                    .limit(limit)\
                    .execute()
                return result.data
            except Exception as e:
                logging.error(f"Error getting HR analysis history: {str(e)}")
                return []