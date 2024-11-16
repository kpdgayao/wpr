# core/validators.py
import re
from typing import List, Dict, Any
import logging

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
    def validate_peer_ratings(ratings: Dict[str, str]) -> Dict[str, int]:
        """Validate peer ratings"""
        validated_ratings = {}
        for peer, rating in ratings.items():
            try:
                # Extract numeric value from rating string (e.g., "1 (Poor)" -> 1)
                numeric_rating = int(rating.split()[0])
                if 1 <= numeric_rating <= 4:
                    validated_ratings[peer] = numeric_rating
            except (ValueError, IndexError):
                logging.warning(f"Invalid rating format for {peer}: {rating}")
                continue
        return validated_ratings