# main.py
import streamlit as st
import logging
from datetime import datetime, timedelta
import anthropic
from typing import Dict, Any
import pandas as pd  

# Import from our modules
from config.settings import Config
from core.database import DatabaseHandler
from core.email_handler import EmailHandler
from core.validators import InputValidator
from core.ai_hr_analyzer import AIHRAnalyzer
from ui.components import UIComponents
from ui.hr_visualizations import HRVisualizations

# At the top of the file, after imports
class Constants:
    MAX_TOKENS = 4000
    AI_MODEL = "claude-3-5-sonnet-20241022"
    LOG_FILE = "wpr.log"
    PAGE_TITLE = "IOL Weekly Productivity Report"
    PAGE_ICON = ":clipboard:"

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
    config: Config
    db: DatabaseHandler
    email_handler: EmailHandler
    ui: UIComponents
    validator: InputValidator
    anthropic_client: anthropic.Client
    ai_hr_analyzer: AIHRAnalyzer

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

    def initialize_session_state(self) -> None:
        """Initialize or reset session state variables"""
        if 'initialized' not in st.session_state:
            current_week = datetime.now().isocalendar()[1]
            current_year = datetime.now().year
            st.session_state.update({
                'initialized': True,
                'selected_name': "",
                'week_number': current_week,
                'year': current_year,  # Add year to session state
                'edit_mode': False,
                'edit_id': None,
                'show_task_section': False,
                'show_project_section': False,
                'show_productivity_section': False,
                'show_peer_evaluation_section': False,
                'submitted': False,
                'form_data': {}
            })

    def _display_week_selector(self):
        """Display week selection widget"""
        current_week = datetime.now().isocalendar()[1]
        current_year = datetime.now().year
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Expand the range to include all weeks from 1 to 52
            week_options = [f"Week {w}" for w in range(1, 53)]
            
            # Find the default index (current week or stored week number)
            default_index = week_options.index(f"Week {st.session_state.week_number}")
            
            selected_week = st.selectbox(
                "Select Week",
                options=week_options,
                index=default_index,
                key='week_selector'
            )
            st.session_state.week_number = int(selected_week.split()[1])
        
        with col2:
            # Add year selection
            year_options = list(range(current_year - 1, current_year + 1))
            selected_year = st.selectbox(
                "Year",
                options=year_options,
                index=year_options.index(current_year),
                key='year_selector'
            )
            st.session_state.year = selected_year

    def _handle_user_submission(self):
        try:
            # Display week selector if not in edit mode
            if not st.session_state.edit_mode:
                self._display_week_selector()
            
            # Check for existing submission BEFORE displaying form
            if not st.session_state.edit_mode:
                existing = self.db.check_existing_submission(
                    st.session_state.selected_name.split(" (")[0],
                    st.session_state.week_number,
                    st.session_state.year
                )
                if existing:
                    st.warning(f"You have already submitted a report for Week {st.session_state.week_number}. You can edit it from the list below.")
                    
            # Display user history
            user_data = self.db.get_user_reports(st.session_state.selected_name)
            if not user_data.empty:
                st.markdown("### Previous Submissions")
                
                # Add debug information
                st.write("Debug: Total submissions found:", len(user_data))
                
                for _, row in user_data.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        created_date = datetime.fromisoformat(row['created_at'].replace('Z', '+00:00'))
                        formatted_date = created_date.strftime("%Y-%m-%d %H:%M")
                        st.write(f"Week {row['Week Number']}, {row['Year']} ({formatted_date})")
                        
                        # Add debug information
                        st.write(f"Debug: Year={row['Year']}, Week={row['Week Number']}")
                        
                    with col2:
                        if st.button("📝 Edit", key=f"edit_{row['id']}"):
                            st.session_state.edit_mode = True
                            st.session_state.edit_id = row['id']
                            self._load_submission_for_edit(row)
                            st.rerun()
                    with col3:
                        if st.button("👁️ View", key=f"view_{row['id']}"):
                            self._display_submission_details(row)
            
            # Get form inputs only if no existing submission
            form_data = self._collect_form_data()
            
            # Handle submission
            if form_data:
                if st.session_state.edit_mode:
                    self._process_edit_submission(form_data)
                else:
                    self._process_form_submission(form_data)
        
        except Exception as e:
            logging.error(f"Error handling submission: {str(e)}")
            st.error("Error processing your submission. Please try again.")

    def _load_submission_for_edit(self, row: pd.Series):
        """Load existing submission data for editing"""
        try:
            # Store the data in session state
            st.session_state.form_data = {
                'completed_tasks': '\n'.join(row.get('Completed Tasks', [])),
                'pending_tasks': '\n'.join(row.get('Pending Tasks', [])),
                'dropped_tasks': '\n'.join(row.get('Dropped Tasks', [])),
                'projects': '\n'.join([f"{p['name']}, {p['completion']}" 
                                     for p in row.get('Projects', [])]),
                'productivity_rating': row.get('Productivity Rating', ''),
                'productivity_suggestions': row.get('Productivity Suggestions', []),
                'productivity_details': row.get('Productivity Details', ''),
                'productive_time': row.get('Productive Time', ''),
                'productive_place': row.get('Productive Place', ''),
                'week_number': row.get('Week Number', st.session_state.week_number)
            }
            
            # Update week number in session state
            st.session_state.week_number = row.get('Week Number', st.session_state.week_number)
            
            logging.info(f"Loaded submission {row.get('id')} for editing")
        except Exception as e:
            logging.error(f"Error loading submission for edit: {str(e)}")
            st.error("Error loading submission data. Please try again.")

    def _display_submission_details(self, row: pd.Series):
        """Display detailed view of a submission"""
        with st.expander("Submission Details", expanded=True):
            st.markdown(f"### Week {row['Week Number']} Report")
            st.write(f"Submitted: {row.get('created_at', 'No date')}")
            
            st.markdown("#### Completed Tasks")
            for task in row.get('Completed Tasks', []):
                st.write(f"- {task}")
            
            st.markdown("#### Pending Tasks")
            for task in row.get('Pending Tasks', []):
                st.write(f"- {task}")
            
            st.markdown("#### Projects")
            for project in row.get('Projects', []):
                st.write(f"- {project['name']}: {project['completion']}% complete")
            
            st.markdown("#### Productivity")
            st.write(f"Rating: {row.get('Productivity Rating', 'Not specified')}")
            st.write(f"Most Productive Time: {row.get('Productive Time', 'Not specified')}")
            st.write(f"Preferred Location: {row.get('Productive Place', 'Not specified')}")

    def _process_edit_submission(self, form_data: Dict[str, Any]):
        """Process edited form submission"""
        try:
            user_email = form_data.pop('user_email')  # Remove email from data dict
            
            with st.spinner("Processing your updated submission..."):
                # Update database
                if not self.db.update_data(form_data, st.session_state.edit_id):
                    st.error("Error updating data in database.")
                    return
                
                # Process submission with AI analysis
                if not self.process_submission(form_data, user_email):
                    st.error("Error processing submission.")
                    return
                
                st.success("WPR updated successfully! Check your email for a summary.")
                
                # Reset edit mode
                st.session_state.edit_mode = False
                st.session_state.edit_id = None
                st.session_state.form_data = {}
                
                # Display HR analysis
                self.display_hr_analysis(form_data['Name'])
                
                # Rerun to refresh the page
                st.rerun()
                
        except Exception as e:
            logging.error(f"Error processing edit submission: {str(e)}")
            st.error("Error processing your submission. Please try again.")

    def _collect_form_data(self):
        """Collect and validate form data"""
        try:
            # Add a cancel button if in edit mode
            if st.session_state.edit_mode:
                if st.button("Cancel Edit"):
                    st.session_state.edit_mode = False
                    st.session_state.edit_id = None
                    st.session_state.form_data = {}
                    st.rerun()
                st.markdown("### Editing Previous Submission")

            # Task Section
            completed_tasks, pending_tasks, dropped_tasks = self.ui.display_task_section(
                default_completed=st.session_state.form_data.get('completed_tasks', ''),
                default_pending=st.session_state.form_data.get('pending_tasks', ''),
                default_dropped=st.session_state.form_data.get('dropped_tasks', '')
            )
            
            # Validate tasks
            if not completed_tasks and not pending_tasks:
                st.warning("Please enter at least one completed or pending task.")
                return None
            
            # Project Section
            projects = self.ui.display_project_section(
                default_projects=st.session_state.form_data.get('projects', '')
            )
            
            # Productivity Section
            productivity_defaults = {
                'productivity_rating': st.session_state.form_data.get('productivity_rating', ''),
                'productivity_suggestions': st.session_state.form_data.get('productivity_suggestions', []),
                'productivity_details': st.session_state.form_data.get('productivity_details', ''),
                'productive_time': st.session_state.form_data.get('productive_time', ''),
                'productive_place': st.session_state.form_data.get('productive_place', '')
            }
            
            (productivity_rating, productivity_suggestions, 
            productivity_details, productive_time, 
            productive_place) = self.ui.display_productivity_section(
                self.config,
                defaults=productivity_defaults
            )
            
            # Validate productivity
            if not productivity_rating:
                st.warning("Please select a productivity rating.")
                return None
            
            # Get actual name without team info
            actual_name = st.session_state.selected_name.split(" (")[0]

            # Peer Evaluation Section
            team = self.config.get_team_for_member(actual_name)  # Use actual_name here
            if not team:
                st.error(f"Team not found for user: {actual_name}")
                return None
                
            teammates = [
                member for member in self.config.teams[team] 
                if member != actual_name  # Compare with actual_name
            ]
            
            peer_ratings = self.ui.display_peer_evaluation_section(
                teammates,
                default_ratings=st.session_state.form_data.get('Peer_Evaluations', {})
            )
            
            # Email input with validation
            user_email = st.text_input(
                "Enter your email address",
                value=st.session_state.form_data.get('user_email', '')
            )
            
            # Update button text based on mode
            button_text = "Update WPR" if st.session_state.edit_mode else "Submit WPR"
            
            if st.button(button_text):
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
                    "Name": actual_name,  # Use actual_name
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

    def setup_page(self) -> None:
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
            
            # Add timeout handling
            with st.spinner("Generating AI analysis..."):
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4000,
                    system=system_prompt,
                    messages=[{
                        "role": "user",
                        "content": f"Please analyze this Weekly Productivity Report and provide comprehensive feedback following the specified format: \n\n{submission_text}"
                    }]
                )
            
            # Validate response
            if not response or not response.content:
                raise ValueError("Empty response from AI")
                
            ai_response = response.content[0].text
            
            # Basic validation of the response format
            if not ("<div" in ai_response and "</div>" in ai_response):
                raise ValueError("AI response format is invalid")
            
            # Log successful analysis
            logging.info("AI analysis generated successfully")
            return ai_response
            
        except Exception as e:
            logging.error(f"AI analysis error: {str(e)}")
            return f"""
            <div style="color: red; padding: 20px; border: 1px solid red; border-radius: 5px;">
                Error generating AI analysis: {str(e)}<br>
                Please contact support for assistance.
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
        """Process new form submission"""
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
                
                # Display HR analysis
                self.display_hr_analysis(form_data['Name'])
                
                # Reset form
                st.session_state.form_data = {}
                
                # Rerun to refresh the page
                st.rerun()
                
        except Exception as e:
            logging.error(f"Error processing form submission: {str(e)}")
            st.error("Error processing your submission. Please try again.")

    def run(self) -> None:
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

if __name__ == "__main__":
    app = WPRApp()
    app.run()