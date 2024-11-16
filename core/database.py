# core/database.py
import logging
import re
from typing import Dict, List, Any
from supabase import create_client
import pandas as pd
from datetime import datetime
import streamlit as st
import json

class DatabaseHandler:
    def __init__(self, supabase_url, supabase_key):
        """Initialize database connection"""
        try:
            self.client = create_client(supabase_url, supabase_key)
            self.table_name = 'wpr_data'
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
            data['Completed Tasks'] = json.dumps(data.get('Completed Tasks', []))
            data['Pending Tasks'] = json.dumps(data.get('Pending Tasks', []))
            data['Dropped Tasks'] = json.dumps(data.get('Dropped Tasks', []))
            data['Productivity Suggestions'] = json.dumps(data.get('Productivity Suggestions', []))
            data['Projects'] = json.dumps(data.get('Projects', []))
            data['Peer_Evaluations'] = json.dumps(data.get('Peer_Evaluations', {}))
            
            # Insert data into Supabase
            result = self.client.table(self.table_name).insert(data).execute()
            logging.info(f"Data saved successfully: {result}")
            return True
        except Exception as e:
            logging.error(f"Error saving data: {str(e)}")
            return False

    def check_existing_submission(self, name: str, week_number: int, year: int) -> bool:
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

    def get_user_reports(self, user_name: str, limit: int = 5) -> pd.DataFrame:
        """Get recent reports for a specific user"""
        try:
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


class InputValidator:
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_tasks(tasks: str) -> List[str]:
        """Validate and clean task input"""
        if not tasks:
            return []
        
        # Split tasks by newline and remove empty lines
        task_list = [task.strip() for task in tasks.split('\n') if task.strip()]
        return task_list

    @staticmethod
    def validate_projects(projects: str) -> List[Dict[str, Any]]:
        """Validate and parse project input"""
        if not projects:
            return []
        
        project_list = []
        for line in projects.split('\n'):
            if line.strip():
                try:
                    name, completion = line.rsplit(',', 1)
                    completion = float(completion.strip())
                    if 0 <= completion <= 100:
                        project_list.append({
                            "name": name.strip(),
                            "completion": completion
                        })
                except ValueError:
                    logging.warning(f"Invalid project format: {line}")
                    continue
        
        return project_list

    @staticmethod
    def validate_peer_ratings(ratings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate peer ratings and format for database"""
        validated_ratings = {}
        for peer, rating in ratings.items():
            try:
                # Extract numeric value from rating string (e.g., "1 (Poor)" -> 1)
                numeric_rating = int(rating.split()[0])
                if 1 <= numeric_rating <= 4:
                    validated_ratings[peer] = {
                        "Peer": peer,
                        "Rating": numeric_rating
                    }
            except (ValueError, IndexError):
                logging.warning(f"Invalid rating format for {peer}: {rating}")
                continue
        return validated_ratings