# config/settings.py
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import logging

class Config:
    def __init__(self):
        """Initialize configuration settings"""
        try:
            # Load environment variables
            load_dotenv()
            
            # Database configuration (required)
            self.SUPABASE_URL = self._get_env_var("SUPABASE_URL")
            self.SUPABASE_KEY = self._get_env_var("SUPABASE_KEY")
            
            # Email configuration (optional)
            self.MAILJET_API_KEY = os.getenv("MAILJET_API_KEY")
            self.MAILJET_API_SECRET = os.getenv("MAILJET_API_SECRET")
            self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
            
            # Teams configuration
            self.TEAMS: Dict[str, List[str]] = {
                "Business Services Team": [
                    "Abigail Visperas", "Cristian Jay Duque", "Justine Louise Ferrer", 
                    "Nathalie Joy Fronda", "Kevin Philip Gayao", "Kurt Lee Gayao", 
                    "Maria Luisa Reynante", "Jester Pedrosa"
                ],
                "Frontend Team": [
                    "Amiel Bryan Gaudia", "George Libatique", "Joshua Aficial"
                ],
                "Backend Team": [
                    "Jeon Angelo Evangelista", "Katrina Gayao", "Renzo Ducusin"
                ]
            }
            
            # Productivity configuration
            self.PRODUCTIVITY_RATINGS: List[str] = [
                '1 - Not Productive',
                '2 - Somewhat Productive',
                '3 - Productive',
                '4 - Very Productive'
            ]
            
            self.PRODUCTIVITY_SUGGESTIONS: List[str] = [
                "More Tools or Resources",
                "More Supervision/Instruction/Guidance",
                "Scheduled Time for Self/Recreation/Rest",
                "Monetary Incentives",
                "Better Time Management",
                "More Teammates",
                "Better Working Environment",
                "More Training",
                "Non-monetary",
                "Workload Balancing",
                "Better Health"
            ]
            
            # Time slots configuration
            self.TIME_SLOTS: List[str] = [
                "8am - 12nn",
                "12nn - 4pm",
                "4pm - 8pm",
                "8pm - 12mn"
            ]
            
            # Work locations
            self.WORK_LOCATIONS: List[str] = ["Office", "Home"]
            
            logging.info("Configuration initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing configuration: {str(e)}")
            raise

    def load_email_config(self) -> bool:
        """
        Load email-related configuration.
        Returns True if successful, False otherwise.
        """
        try:
            self.MAILJET_API_KEY = self._get_env_var("MAILJET_API_KEY")
            self.MAILJET_API_SECRET = self._get_env_var("MAILJET_API_SECRET")
            self.ANTHROPIC_API_KEY = self._get_env_var("ANTHROPIC_API_KEY")
            return True
        except ValueError as e:
            logging.warning(f"Email configuration not loaded: {str(e)}")
            return False

    def _get_env_var(self, var_name: str) -> str:
        """Get environment variable with error handling"""
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Environment variable {var_name} not found")
        return value

    def get_all_team_members(self) -> List[str]:
        """Returns a list of all team members with their team names"""
        try:
            team_members = []
            for team, members in self.TEAMS.items():
                for member in members:
                    team_members.append(f"{member} ({team})")
            return sorted(team_members)
        except Exception as e:
            logging.error(f"Error getting team members: {str(e)}")
            return []

    def get_team_for_member(self, member_name: str) -> Optional[str]:
        """Returns the team name for a given member"""
        try:
            # Extract just the name without the team info in parentheses
            actual_name = member_name.split(" (")[0] if " (" in member_name else member_name
            
            for team, members in self.TEAMS.items():
                if actual_name in members:
                    return team
            logging.warning(f"No team found for member: {actual_name}")
            return None
        except Exception as e:
            logging.error(f"Error getting team for member {member_name}: {str(e)}")
            return None