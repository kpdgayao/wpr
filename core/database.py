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
            self.table_name = 'wpr_data'
            self.hr_table_name = 'hr_analysis'
            
            # Add unique constraint on Name, Week Number, and Year if it doesn't exist
            # Note: This would need to be done at the Supabase database level
            # CREATE UNIQUE INDEX IF NOT EXISTS unique_weekly_submission 
            # ON wpr_data (Name, "Week Number", Year);
            
            logging.info("Database connection initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize database connection: {str(e)}")
            raise

    def save_data(self, data: Dict[str, Any]) -> bool:
        try:
            # Extract actual name without team info if present
            if 'Name' in data:
                data['Name'] = data['Name'].split(" (")[0] if " (" in data['Name'] else data['Name']
            
            # Check for existing submission AFTER name is processed
            existing = self.check_existing_submission(
                data['Name'],
                data['Week Number'],
                data['Year']
            )
            if existing:
                logging.warning(f"Duplicate submission detected for {data['Name']}, Week {data['Week Number']}")
                return False

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

    def get_user_reports(self, user_name: str) -> pd.DataFrame:
        """Get reports for a specific user, ordered by most recent first"""
        try:
            # Extract actual name without team info
            actual_name = user_name.split(" (")[0] if " (" in user_name else user_name
            
            logging.info(f"Fetching reports for user: {actual_name}")
            
            # Build query to get all submissions ordered by year and week number
            result = self.client.table(self.table_name)\
                .select("*")\
                .eq("Name", actual_name)\
                .order('Year', desc=True)\
                .order('Week Number', desc=True)\
                .execute()
            
            logging.info(f"Found {len(result.data)} reports for user {actual_name}")
            
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
            
            # Convert to DataFrame and sort by Year and Week Number
            df = pd.DataFrame(data)
            if not df.empty:
                df = df.sort_values(by=['Year', 'Week Number'], ascending=[False, False])
            
            return df
                
        except Exception as e:
            logging.error(f"Error getting user reports: {str(e)}")
            return pd.DataFrame()

    def check_existing_submission(self, name: str, week_number: int, year: int) -> bool:
        """Check if user has already submitted for the given week"""
        try:
            # Extract actual name without team info
            actual_name = name.split(" (")[0] if " (" in name else name
            
            logging.info(f"Checking submission for {actual_name}, Week {week_number}, Year {year}")
            result = self.client.table(self.table_name)\
                .select("*")\
                .eq("Name", actual_name)\
                .eq("Week Number", week_number)\
                .eq("Year", year)\
                .execute()
                
            exists = len(result.data) > 0
            logging.info(f"Submission exists: {exists} for {actual_name}, Week {week_number}, Year {year}")
            return exists
            
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
            # Create database object matching the actual schema
            db_data = {
                'employee_name': analysis_data.get('employee_name'),
                'week_number': analysis_data.get('week_number'),
                'year': analysis_data.get('year'),
                # Change from analysis_times to analysis_timestamp
                'analysis_timestamp': datetime.now().isoformat(),
                'performance_metrics': json.dumps(analysis_data.get('performance_metrics', {})),
                'skill_assessment': json.dumps(analysis_data.get('skill_assessment', {})),
                'wellness_indicators': json.dumps(analysis_data.get('wellness_indicators', {})),
                'growth_recommendations': json.dumps(analysis_data.get('growth_recommendations', {})),
                'team_dynamics': json.dumps(analysis_data.get('team_dynamics', {})),
                'risk_factors': json.dumps(analysis_data.get('risk_factors', {}))
            }
            
            # Validate required fields
            required_fields = ['employee_name', 'week_number', 'year']
            for field in required_fields:
                if not db_data.get(field):
                    raise ValueError(f"Missing required field: {field}")
                    
            # Ensure numeric fields are integers
            try:
                db_data['week_number'] = int(float(str(db_data['week_number'])))
                db_data['year'] = int(float(str(db_data['year'])))
            except (ValueError, TypeError) as e:
                logging.error(f"Error converting numeric fields: {str(e)}")
                raise ValueError("Week number and year must be valid numbers")
            
            # Insert into database
            result = self.client.table(self.hr_table_name).insert(db_data).execute()
            logging.info(f"HR analysis saved successfully for {db_data['employee_name']}")
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

    def update_data(self, data: Dict[str, Any], record_id: int) -> bool:
        """Update existing WPR data"""
        try:
            # Update timestamp
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
            
            logging.info(f"Updating data for {data.get('Name')}, Week {data.get('Week Number')}")
            result = self.client.table(self.table_name)\
                .update(data)\
                .eq('id', record_id)\
                .execute()
            logging.info(f"Data updated successfully: {result}")
            return True
        except Exception as e:
            logging.error(f"Error updating data: {str(e)}")
            if hasattr(e, '__dict__'):
                logging.error(f"Detailed error: {e.__dict__}")
            return False

    def get_submission_by_id(self, record_id: int) -> Dict[str, Any]:
        """Get specific submission by ID"""
        try:
            result = self.client.table(self.table_name)\
                .select("*")\
                .eq("id", record_id)\
                .execute()
            
            if not result.data:
                return {}
                
            # Convert JSON strings back to Python objects
            data = result.data[0]
            json_fields = [
                'Completed Tasks', 'Pending Tasks', 'Dropped Tasks',
                'Productivity Suggestions', 'Projects', 'Peer_Evaluations'
            ]
            
            for field in json_fields:
                if field in data and isinstance(data[field], str):
                    try:
                        data[field] = json.loads(data[field])
                    except json.JSONDecodeError:
                        data[field] = []
            
            return data
        except Exception as e:
            logging.error(f"Error getting submission: {str(e)}")
            return {}  
        
    def debug_check_database(self, user_name: str) -> None:
        """Debug method to check database contents"""
        try:
            actual_name = user_name.split(" (")[0] if " (" in user_name else user_name
            
            # Get all records for the user
            result = self.client.table(self.table_name)\
                .select("*")\
                .eq("Name", actual_name)\
                .execute()
                
            logging.info(f"DEBUG: Found {len(result.data)} total records for {actual_name}")
            
            # Log each record
            for record in result.data:
                logging.info(f"DEBUG: Record - Week {record.get('Week Number')}, "
                            f"Year {record.get('Year')}, "
                            f"ID {record.get('id')}, "
                            f"Created {record.get('created_at')}")
                
        except Exception as e:
            logging.error(f"Debug check failed: {str(e)}")

    def debug_check_week_range(self, user_name: str, start_week: int, end_week: int, year: int) -> None:
        """Debug method to check specific week range"""
        try:
            actual_name = user_name.split(" (")[0] if " (" in user_name else user_name
            
            result = self.client.table(self.table_name)\
                .select("*")\
                .eq("Name", actual_name)\
                .eq("Year", year)\
                .gte("Week Number", start_week)\
                .lte("Week Number", end_week)\
                .execute()
                
            logging.info(f"DEBUG: Checking weeks {start_week}-{end_week} for {actual_name}")
            logging.info(f"DEBUG: Found {len(result.data)} records in range")
            
            for record in result.data:
                logging.info(f"DEBUG: Week {record.get('Week Number')} "
                            f"(ID: {record.get('id')}, "
                            f"Created: {record.get('created_at')})")
                
        except Exception as e:
            logging.error(f"Debug week range check failed: {str(e)}")
    