# config/settings.py
import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Database configuration
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        # Email configuration
        self.mailjet_api_key = os.getenv("MAILJET_API_KEY")
        self.mailjet_api_secret = os.getenv("MAILJET_API_SECRET")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Teams configuration
        self.teams = {
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
        self.productivity_ratings = [
            '1 - Not Productive',
            '2 - Somewhat Productive',
            '3 - Productive',
            '4 - Very Productive'
        ]
        
        self.productivity_suggestions = [
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
        self.time_slots = [
            "8am - 12nn",
            "12nn - 4pm",
            "4pm - 8pm",
            "8pm - 12mn"
        ]
        
        # Work locations
        self.work_locations = ["Office", "Home"]

    def get_all_team_members(self):
        """Returns a list of all team members with their team names"""
        return [
            f"{name} ({team})" 
            for team, members in self.teams.items() 
            for name in members
        ]

    def get_team_for_member(self, member_name):
        """Returns the team name for a given member"""
        for team, members in self.teams.items():
            if member_name in members:
                return team
        return None