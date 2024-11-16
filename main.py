# main.py
import streamlit as st
import logging
from datetime import datetime
import anthropic
from typing import Dict, Any

# Import from our modules
from config.settings import Config
from core.database import DatabaseHandler
from core.email_handler import EmailHandler
from core.validators import InputValidator
from core.ai_hr_analyzer import AIHRAnalyzer
from ui.components import UIComponents
from ui.hr_visualizations import HRVisualizations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('wpr.log')
    ]
)

class WPRApp:
    def __init__(self):
        """Initialize the WPR application"""
        try:
            # Load configuration
            self.config = Config()
            
            # Initialize components
            self.db = DatabaseHandler(self.config.supabase_url, self.config.supabase_key)
            self.email_handler = EmailHandler(
                self.config.mailjet_api_key, 
                self.config.mailjet_api_secret
            )
            self.ui = UIComponents()
            self.validator = InputValidator()
            
            # Set up AI components
            if not self.config.anthropic_api_key:
                raise ValueError("Anthropic API key not found in configuration")
                
            self.anthropic_client = anthropic.Client(api_key=self.config.anthropic_api_key)
            self.ai_hr_analyzer = AIHRAnalyzer(self.config.anthropic_api_key)
            
            logging.info("WPR application initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing WPR application: {str(e)}")
            raise

    def initialize_session_state(self):
        """Initialize or reset session state variables"""
        if 'initialized' not in st.session_state:
            st.session_state.update({
                'initialized': True,
                'selected_name': "",
                'week_number': datetime.now().isocalendar()[1],
                'show_task_section': False,
                'show_project_section': False,
                'show_productivity_section': False,
                'show_peer_evaluation_section': False,
                'submitted': False
            })

    def setup_page(self):
        """Set up the Streamlit page configuration"""
        st.set_page_config(
            page_title="IOL Weekly Productivity Report",
            page_icon=":clipboard:",
            layout="wide"
        )
        self.ui.load_custom_css()

    def _prepare_submission_text(self, data: Dict[str, Any]) -> str:
        """Prepare submission text for AI analysis"""
        return f"""
        Name: {data['Name']}
        Team: {data['Team']}
        Week Number: {data['Week Number']}
        Year: {data['Year']}
        
        Completed Tasks: {data['Completed Tasks']}
        Pending Tasks: {data['Pending Tasks']}
        Dropped Tasks: {data['Dropped Tasks']}
        
        Projects: {data['Projects']}
        
        Productivity Rating: {data['Productivity Rating']}
        Productivity Suggestions: {data['Productivity Suggestions']}
        Productivity Details: {data['Productivity Details']}
        
        Most Productive Time: {data['Productive Time']}
        Preferred Work Location: {data['Productive Place']}
        
        Peer Evaluations: {data['Peer_Evaluations']}
        """

    def _get_system_prompt(self, week_number: int) -> str:
        """Get enhanced system prompt for AI analysis"""
        return f"""You are an empathetic HR productivity expert and career coach for IOL Inc., a dynamic systems development startup. 
        Your role is to analyze Weekly Productivity Reports (WPR) and provide personalized, actionable feedback.

        Guidelines for Analysis:

        1. TONE AND APPROACH:
        - Maintain a supportive, encouraging, and professional tone
        - Balance praise with constructive feedback
        - Use the employee's name naturally throughout the response
        - Frame challenges as growth opportunities

        2. STRUCTURE YOUR RESPONSE AS FOLLOWS:

        <div style="font-family: Arial, sans-serif;">
            <h2 style="color: #2E86C1;">Weekly Performance Analysis - Week {week_number} 📊</h2>
            
            <h3 style="color: #2471A3;">🌟 Achievement Highlights</h3>
            [Analyze and celebrate:
            - Task completion rate
            - Project progress
            - Notable accomplishments
            - Productivity level]

            <h3 style="color: #2471A3;">📈 Performance Metrics</h3>
            [Provide specific metrics:
            - Task completion ratio
            - Project completion percentages
            - Productivity rating analysis
            - Week-over-week comparison if available]

            <h3 style="color: #2471A3;">💡 Growth Opportunities</h3>
            [Offer constructive feedback:
            - Areas for improvement
            - Skill development suggestions
            - Resource recommendations
            - Time management strategies]

            <h3 style="color: #2471A3;">🎯 Action Plan for Next Week</h3>
            <ol>
                [Provide 3-5 specific, actionable recommendations based on:
                - Current task status
                - Project priorities
                - Productivity patterns
                - Personal work preferences]
            </ol>

            <h3 style="color: #2471A3;">🤝 Team Collaboration Insights</h3>
            [Analyze:
            - Peer evaluation patterns
            - Team dynamics
            - Collaboration opportunities
            - Knowledge sharing suggestions]

            <h3 style="color: #2471A3;">⚡ Productivity Optimization</h3>
            [Provide specific suggestions based on:
            - Reported productive hours
            - Preferred work location
            - Productivity challenges
            - Suggested improvements]

            <h3 style="color: #2471A3;">🌈 Wellness Check</h3>
            [Address:
            - Work-life balance
            - Stress management
            - Environmental preferences
            - Support needs]

            <h3 style="color: #2471A3;">📋 Priority Management</h3>
            <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
                <tr style="background-color: #2E86C1; color: white;">
                    <th style="padding: 10px; border: 1px solid #85C1E9;">Priority Level</th>
                    <th style="padding: 10px; border: 1px solid #85C1E9;">Action Items</th>
                    <th style="padding: 10px; border: 1px solid #85C1E9;">Timeline</th>
                </tr>
                [Add 3-4 rows of prioritized tasks and projects]
            </table>

            <h3 style="color: #2471A3;">🎉 Motivation & Recognition</h3>
            [Provide:
            - Specific recognition of achievements
            - Encouragement for challenges
            - Connection to company goals
            - Personal growth acknowledgment]

            <div style="background-color: #EBF5FB; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <h4 style="color: #2E86C1; margin-top: 0;">💪 Success Strategies for Week {week_number + 1}</h4>
                <ol>
                    [List 3-5 specific, actionable strategies based on the analysis]
                </ol>
            </div>

            <div style="background-color: #D4E6F1; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <h4 style="color: #2E86C1; margin-top: 0;">📚 Recommended Resources</h4>
                [Suggest specific tools, training, or resources based on needs]
            </div>

            <p style="color: #2E86C1; font-weight: bold; margin-top: 20px;">
                Keep up the great work! Remember, progress is a journey, not a destination. 
                We're here to support your growth and success at IOL Inc.
            </p>
        </div>

        IMPORTANT GUIDELINES:
        1. Always analyze the data in context of previous weeks if available
        2. Provide specific, actionable feedback rather than generic advice
        3. Address both technical and soft skills development
        4. Consider team dynamics and collaboration patterns
        5. Focus on both immediate improvements and long-term growth
        6. Maintain a balance between task completion and quality of work
        7. Consider the employee's preferred working style and environment
        8. Include both individual and team-based recommendations
        9. Address any concerns while maintaining a positive, solution-focused approach
        10. Ensure all feedback aligns with IOL Inc.'s goals and values

        Remember to maintain a supportive and professional tone throughout the analysis.
        """

    def _get_ai_analysis(self, submission_text: str) -> str:
        """Get AI analysis of the submission"""
        try:
            system_prompt = self._get_system_prompt(st.session_state.week_number)
            
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,  # Increased token limit for comprehensive analysis
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Please analyze this Weekly Productivity Report and provide comprehensive feedback following the specified format: \n\n{submission_text}"
                }]
            )
            
            # Log successful analysis
            logging.info("AI analysis generated successfully")
            return response.content[0].text
        except Exception as e:
            logging.error(f"AI analysis error: {str(e)}")
            return """
            <div style="color: red; padding: 20px; border: 1px solid red; border-radius: 5px;">
                Error generating AI analysis. Please contact support for assistance.
            </div>
            """

def display_hr_analysis(self, employee_name: str):
    """Display HR analysis dashboard"""
    try:
        with st.spinner("Loading HR analysis..."):
            # Get latest HR analysis
            hr_history = self.db.get_hr_analysis_history(employee_name)
            if not hr_history:
                st.warning("No HR analysis history found.")
                return

            hr_analysis = hr_history[0]
            historical_data = hr_history
            
            # Display dashboard
            HRVisualizations.display_hr_dashboard(hr_analysis, historical_data)
            
            logging.info(f"HR analysis displayed successfully for {employee_name}")
    except Exception as e:
        logging.error(f"Error displaying HR analysis: {str(e)}")
        st.error("Error displaying HR analysis dashboard.")

def process_submission(self, data: Dict[str, Any], user_email: str) -> bool:
    try:
        # Generate HR analysis
        hr_analysis = self.ai_hr_analyzer.generate_hr_analysis(data)
        
        # Save HR analysis to database
        self.db.save_hr_analysis(hr_analysis)
        
        # Send HR analysis email
        hr_email_content = self.email_handler.format_hr_analysis_email(
            data['Name'],
            data['Week Number'],
            hr_analysis
        )
        
        self.email_handler.send_email(
            to_email=user_email,
            to_name=data['Name'],
            subject=f"HR Analysis Report - Week {data['Week Number']}",
            html_content=hr_email_content
        )
        
        # Display HR analysis dashboard
        self.display_hr_analysis(data['Name'])
        
        return True
    except Exception as e:
        logging.error(f"Error processing submission: {str(e)}")
        return False

def _process_form_submission(self, form_data: Dict[str, Any]):
    """Process the form submission"""
    try:
        user_email = form_data.pop('user_email')  # Remove email from data dict
        
        with st.spinner("Processing your submission..."):
            # Save to database
            if not self.db.save_data(form_data):
                st.error("Error saving data to database.")
                return
            
            # Process submission with AI analysis
            if not self.process_submission(form_data, user_email):
                st.error("Error processing submission.")
                return
            
            st.success("WPR submitted successfully! Check your email for a summary.")
            st.session_state.submitted = True
            
            # Display HR analysis
            self.display_hr_analysis(form_data['Name'])
            
    except Exception as e:
        logging.error(f"Error processing form submission: {str(e)}")
        st.error("Error processing your submission. Please try again.")

def run(self):
    """Run the WPR application"""
    try:
        self.setup_page()
        self.initialize_session_state()
        
        # Display header
        self.ui.display_header(st.session_state.week_number)
        
        # Name selection
        st.session_state.selected_name = st.selectbox(
            "Select Your Name",
            options=[""] + self.config.get_all_team_members(),
            format_func=lambda x: "Select your name" if x == "" else x
        )
        
        if st.session_state.selected_name:
            self._handle_user_submission()
    
    except Exception as e:
        logging.error(f"Application error: {str(e)}")
        st.error("An error occurred. Please try again or contact support.")

def _handle_user_submission(self):
    """Handle user submission logic"""
    try:
        # Check for existing submission
        if self.db.check_existing_submission(
            st.session_state.selected_name,
            st.session_state.week_number,
            datetime.now().year
        ):
            st.warning("You have already submitted a report for this week.")
            return
        
        # Display user history
        user_data = self.db.get_user_reports(st.session_state.selected_name)
        self.ui.display_user_history(user_data)
        
        # Get form inputs
        form_data = self._collect_form_data()
        
        # Handle submission
        if form_data:
            self._process_form_submission(form_data)
    
    except Exception as e:
        logging.error(f"Error handling submission: {str(e)}")
        st.error("Error processing your submission. Please try again.")

def _collect_form_data(self):
    """Collect and validate form data"""
    try:
        # Task Section
        completed_tasks, pending_tasks, dropped_tasks = self.ui.display_task_section()
        
        # Validate tasks
        if not completed_tasks and not pending_tasks:
            st.warning("Please enter at least one completed or pending task.")
            return None
        
        # Project Section
        projects = self.ui.display_project_section()
        
        # Productivity Section
        (productivity_rating, productivity_suggestions, 
         productivity_details, productive_time, 
         productive_place) = self.ui.display_productivity_section(self.config)
        
        # Validate productivity
        if not productivity_rating:
            st.warning("Please select a productivity rating.")
            return None
        
        # Peer Evaluation Section
        team = self.config.get_team_for_member(st.session_state.selected_name)
        if not team:
            st.error("Team not found for selected user.")
            return None
            
        teammates = [
            member for member in self.config.teams[team] 
            if member != st.session_state.selected_name
        ]
        peer_ratings = self.ui.display_peer_evaluation_section(teammates)
        
        # Email input with validation
        user_email = st.text_input("Enter your email address")
        
        if st.button("Submit WPR"):
            # Validate email
            if not user_email or not self.validator.validate_email(user_email):
                st.error("Please enter a valid email address")
                return None
            
            # Validate peer ratings
            if not peer_ratings and teammates:
                st.warning("Please provide at least one peer evaluation.")
                return None
            
            # Create and return form data
            form_data = {
                "Name": st.session_state.selected_name,
                "Team": team,
                "Week Number": st.session_state.week_number,
                "Year": datetime.now().year,
                "Completed Tasks": self.validator.validate_tasks(completed_tasks),
                "Pending Tasks": self.validator.validate_tasks(pending_tasks),
                "Dropped Tasks": self.validator.validate_tasks(dropped_tasks),
                "Projects": self.validator.validate_projects(projects),
                "Productivity Rating": productivity_rating,
                "Productivity Suggestions": productivity_suggestions,
                "Productivity Details": productivity_details,
                "Productive Time": productive_time,
                "Productive Place": productive_place,
                "Peer_Evaluations": self.validator.validate_peer_ratings(peer_ratings),
                "user_email": user_email
            }
            
            # Log submission attempt
            logging.info(f"Form data collected for {form_data['Name']} - Week {form_data['Week Number']}")
            
            return form_data
        
        return None
    
    except Exception as e:
        logging.error(f"Error collecting form data: {str(e)}")
        st.error("Error collecting form data. Please try again.")
        return None
    
    except Exception as e:
        logging.error(f"Error collecting form data: {str(e)}")
        st.error("Error collecting form data. Please try again.")
        return None

if __name__ == "__main__":
    app = WPRApp()
    app.run()