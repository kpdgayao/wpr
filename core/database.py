# core/database.py
import logging
from typing import Dict, List, Any
from supabase import create_client
import pandas as pd
from datetime import datetime
import streamlit as st
import json

class DatabaseHandler:
    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize database connection"""
        try:
            self.client = create_client(supabase_url, supabase_key)
            self.table_name = 'wpr_data'  # Updated table name
            self.hr_table_name = 'hr_analysis'
            logging.info("Database connection initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize database connection: {str(e)}")
            raise

    def save_data(self, data: Dict[str, Any]) -> bool:
        """Save WPR data to database"""
        try:
            # Add timestamp to data
            data['created_at'] = datetime.now().isoformat()
            
            # Calculate number of tasks
            data['Number of Completed Tasks'] = len(data.get('Completed Tasks', []))
            data['Number of Pending Tasks'] = len(data.get('Pending Tasks', []))
            data['Number of Dropped Tasks'] = len(data.get('Dropped Tasks', []))
            
            # Convert lists to JSONB format
            json_fields = [
                'Completed Tasks', 'Pending Tasks', 'Dropped Tasks',
                'Productivity Suggestions', 'Projects', 'Peer_Evaluations'
            ]
            
            for field in json_fields:
                if field in data:
                    data[field] = json.dumps(data[field])
            
            logging.info(f"Saving data for {data.get('Name')}, Week {data.get('Week Number')}")
            result = self.client.table(self.table_name).insert(data).execute()
            logging.info(f"Data saved successfully: {result}")
            return True
        except Exception as e:
            logging.error(f"Error saving data: {str(e)}")
            if hasattr(e, '__dict__'):
                logging.error(f"Detailed error: {e.__dict__}")
            return False

    def load_data(self) -> pd.DataFrame:
        """Load all WPR data"""
        try:
            result = self.client.table(self.table_name).select("*").execute()
            data = result.data
            
            # Convert JSON strings back to Python objects
            for row in data:
                for field in ['Completed Tasks', 'Pending Tasks', 'Dropped Tasks',
                            'Productivity Suggestions', 'Projects', 'Peer_Evaluations']:
                    if field in row and isinstance(row[field], str):
                        try:
                            row[field] = json.loads(row[field])
                        except json.JSONDecodeError:
                            row[field] = []
            
            return pd.DataFrame(data)
        except Exception as e:
            logging.error(f"Error loading data: {str(e)}")
            return pd.DataFrame()

    def get_user_reports(self, user_name: str, limit: int = 5) -> pd.DataFrame:
        """Get recent reports for a specific user"""
        try:
            logging.info(f"Fetching reports for user: {user_name}")
            result = self.client.table(self.table_name)\
                .select("*")\
                .eq("Name", user_name)\
                .order('created_at', desc=True)\
                .limit(limit)\
                .execute()
            
            # Convert JSONB strings back to Python objects
            data = result.data
            for row in data:
                for field in ['Completed Tasks', 'Pending Tasks', 'Dropped Tasks',
                            'Productivity Suggestions', 'Projects', 'Peer_Evaluations']:
                    if field in row and isinstance(row[field], str):
                        try:
                            row[field] = json.loads(row[field])
                        except json.JSONDecodeError:
                            logging.warning(f"Failed to parse JSON for {field} in row {row.get('id')}")
                            row[field] = []
            
            return pd.DataFrame(data)
        except Exception as e:
            logging.error(f"Error getting user reports: {str(e)}")
            return pd.DataFrame()

    def check_existing_submission(self, name: str, week_number: int, year: int) -> bool:
        """Check if user has already submitted for the given week"""
        try:
            logging.info(f"Checking submission for {name}, Week {week_number}, Year {year}")
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

    def get_team_reports(self, team_name: str, week_number: int = None) -> pd.DataFrame:
        """Get reports for an entire team"""
        try:
            query = self.client.table(self.table_name)\
                .select("*")\
                .eq("Team", team_name)
            
            if week_number:
                query = query.eq("Week Number", week_number)
                
            result = query.execute()
            data = result.data
            
            # Convert JSON strings back to Python objects
            for row in data:
                for field in ['Completed Tasks', 'Pending Tasks', 'Dropped Tasks',
                            'Productivity Suggestions', 'Projects', 'Peer_Evaluations']:
                    if field in row and isinstance(row[field], str):
                        try:
                            row[field] = json.loads(row[field])
                        except json.JSONDecodeError:
                            row[field] = []
            
            return pd.DataFrame(data)
        except Exception as e:
            logging.error(f"Error getting team reports: {str(e)}")
            return pd.DataFrame()

    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_productivity_stats(self, team_name: str = None) -> Dict[str, Any]:
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

    def save_hr_analysis(self, analysis_data: Dict[str, Any]) -> bool:
        """Save HR analysis to database"""
        try:
            # Add timestamp if not present
            if 'analysis_timestamp' not in analysis_data:
                analysis_data['analysis_timestamp'] = datetime.now().isoformat()
            
            # Ensure all JSON fields are properly serialized
            json_fields = [
                'performance_metrics', 'skill_assessment', 'wellness_indicators',
                'growth_recommendations', 'team_dynamics', 'risk_factors'
            ]
            
            for field in json_fields:
                if field in analysis_data and not isinstance(analysis_data[field], str):
                    analysis_data[field] = json.dumps(analysis_data[field])
            
            result = self.client.table(self.hr_table_name).insert(analysis_data).execute()
            logging.info(f"HR analysis saved successfully: {result}")
            return True
        except Exception as e:
            logging.error(f"Error saving HR analysis: {str(e)}")
            return False

    def get_hr_analysis_history(self, employee_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get historical HR analysis for an employee"""
        try:
            result = self.client.table(self.hr_table_name)\
                .select("*")\
                .eq("employee_name", employee_name)\
                .order('analysis_timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            # Parse JSON fields
            data = result.data
            json_fields = [
                'performance_metrics', 'skill_assessment', 'wellness_indicators',
                'growth_recommendations', 'team_dynamics', 'risk_factors'
            ]
            
            for row in data:
                for field in json_fields:
                    if field in row and isinstance(row[field], str):
                        try:
                            row[field] = json.loads(row[field])
                        except json.JSONDecodeError:
                            logging.warning(f"Failed to parse JSON for {field} in row {row.get('id')}")
                            row[field] = {}
            
            return data
        except Exception as e:
            logging.error(f"Error getting HR analysis history: {str(e)}")
            return []