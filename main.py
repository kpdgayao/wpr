# main.py
import streamlit as st
import logging
from datetime import datetime, timedelta
import anthropic
from typing import Dict, Any
import pandas as pd  
import time  # Import time module
from utils.error_handler import handle_exceptions, format_error_message
from utils.logging_config import setup_logging

# Initialize logging
setup_logging()

# Import from our modules
from config.settings import Config
from config.constants import Constants
from core.database import DatabaseHandler
from core.email_handler import EmailHandler
from core.validators import InputValidator
from core.ai_hr_analyzer import AIHRAnalyzer
from ui.components import UIComponents
from ui.hr_visualizations import HRVisualizations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            Constants.LOG_FILE,
            maxBytes=1024 * 1024,  # 1MB
            backupCount=5,
            encoding='utf-8'
        )
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
            self.db = DatabaseHandler(self.config.SUPABASE_URL, self.config.SUPABASE_KEY)
            
            # Initialize email handler if credentials are available
            logging.info("Checking Mailjet credentials...")
            if hasattr(self.config, 'MAILJET_API_KEY') and hasattr(self.config, 'MAILJET_API_SECRET'):
                if self.config.MAILJET_API_KEY and self.config.MAILJET_API_SECRET:
                    logging.info("Mailjet credentials found, initializing email handler...")
                    try:
                        self.email_handler = EmailHandler(
                            self.config.MAILJET_API_KEY,
                            self.config.MAILJET_API_SECRET
                        )
                        logging.info("Email handler initialized successfully")
                    except Exception as e:
                        logging.error(f"Failed to initialize email handler: {str(e)}")
                        self.email_handler = None
                else:
                    logging.warning("Mailjet credentials are empty")
                    self.email_handler = None
            else:
                logging.warning("Mailjet credential attributes not found in config")
                self.email_handler = None
            
            # Set up AI components
            if not self.config.ANTHROPIC_API_KEY:
                logging.warning("Anthropic API key not found - AI features will be disabled")
                self.anthropic_client = None
                self.ai_hr_analyzer = None
            else:
                self.anthropic_client = anthropic.Client(api_key=self.config.ANTHROPIC_API_KEY)
                self.ai_hr_analyzer = AIHRAnalyzer(anthropic_api_key=self.config.ANTHROPIC_API_KEY)
                logging.info("AI components initialized successfully")
            
            # Initialize UI components
            self.ui = UIComponents()
            self.validator = InputValidator()
            
            logging.info("WPR application initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing WPR application: {str(e)}")
            raise

    def initialize_session_state(self):
        """Initialize or reset session state variables"""
        if 'submitted' not in st.session_state:
            st.session_state.submitted = False
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = False
        if 'edit_id' not in st.session_state:
            st.session_state.edit_id = None
        if 'form_data' not in st.session_state:
            st.session_state.form_data = {}
        if 'success_message' not in st.session_state:
            st.session_state.success_message = None
            
        # Use the provided current time
        current_date = datetime.now()
        current_week = current_date.isocalendar()[1]
        current_year = current_date.year
        
        if 'week_number' not in st.session_state:
            st.session_state.week_number = current_week
        if 'selected_name' not in st.session_state:
            st.session_state.selected_name = ""
        if 'initialized' not in st.session_state:
            st.session_state.update({
                'initialized': True,
                'year': current_year,  # Add year to session state
                'show_task_section': False,
                'show_project_section': False,
                'show_productivity_section': False,
                'show_peer_section': False,
            })

    @handle_exceptions(error_types=(Exception,))
    def _handle_user_submission(self):
        """Handle user form submission"""
        try:
            # Create placeholders for messages
            message_container = st.container()
            
            # Show any existing success message
            if st.session_state.success_message:
                message_container.success(st.session_state.success_message)
                # Clear the message after showing it
                st.session_state.success_message = None
                return

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
                
                # Create a container for all submissions
                with st.container():
                    for _, row in user_data.iterrows():
                        # Create a container for each submission
                        with st.container():
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                year = int(row['Year'])
                                week = int(row['Week Number'])
                                created_date = datetime.fromisoformat(str(row['created_at']).replace('Z', '+00:00'))
                                formatted_date = created_date.strftime("%Y-%m-%d %H:%M")
                                
                                st.markdown(f"""
                                    #### Week {week}, {year}
                                    Submitted: {formatted_date}
                                """)
                            
                            with col2:
                                if st.button("📝 Edit", key=f"edit_{row['id']}"):
                                    st.session_state.edit_mode = True
                                    st.session_state.edit_id = row['id']
                                    self._load_submission_for_edit(row)
                                    st.rerun()
                            
                            with col3:
                                if st.button("👁️ View", key=f"view_{row['id']}"):
                                    self._display_submission_details(row)
                            
                            st.divider()
            
            # Get form inputs
            form_data = self._collect_form_data()
            
            # Handle submission
            if form_data:
                if st.session_state.edit_mode:
                    self._process_edit_submission(form_data)
                else:
                    try:
                        # 1. Save data to database first
                        data = self.db.save_data(form_data)
                        logging.info(f"Data saved successfully: {data}")
                        
                        # 2. Show processing message
                        with message_container:
                            st.info("⏳ Processing your submission...")
                        
                        # 3. Generate AI analysis
                        ai_analysis = None
                        if self.ai_hr_analyzer is not None:
                            try:
                                analysis_result = self.ai_hr_analyzer.generate_hr_analysis(form_data)
                                if analysis_result:
                                    ai_analysis = analysis_result.get('analysis_content')
                                    logging.info("AI analysis generated successfully")
                            except Exception as e:
                                logging.warning(f"Failed to generate HR analysis: {str(e)}")
                        
                        # 4. Send email notification
                        email_sent = False
                        if self.email_handler:
                            try:
                                email_sent = self.email_handler.send_wpr_notification(
                                    to_email=form_data['user_email'],
                                    to_name=form_data['Name'],
                                    week_number=form_data['Week Number'],
                                    year=form_data['Year'],
                                    ai_analysis=ai_analysis
                                )
                            except Exception as e:
                                logging.error(f"Failed to send email: {str(e)}")
                        
                        # 5. Set success message based on email status
                        success_msg = "✅ WPR submitted successfully!"
                        if email_sent:
                            success_msg += " An email confirmation has been sent to your inbox."
                        
                        # 6. Update session state
                        st.session_state.submitted = True
                        st.session_state.form_data = {}
                        st.balloons()
                        
                        # 7. Show success message
                        with message_container:
                            st.success(success_msg)
                        
                        return True
                        
                    except Exception as e:
                        logging.error(f"Error processing submission: {str(e)}")
                        with message_container:
                            st.error("❌ Error processing your submission. Please try again.")
                        return False
        
        except Exception as e:
            logging.error(f"Error in form submission: {str(e)}")
            with message_container:
                st.error("An unexpected error occurred. Please try again.")

    def _display_week_selector(self):
        """Display week selection widget"""
        current_date = datetime.now()  # Use current date
        current_week = current_date.isocalendar()[1]
        current_year = current_date.year
        
        # Update session state with current week if not already set
        if 'week_number' not in st.session_state:
            st.session_state.week_number = current_week
        
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
            # Add year selection including current year and adjacent years
            year_options = [current_year - 1, current_year, current_year + 1]
            
            # Initialize year in session state if not set
            if 'year' not in st.session_state:
                st.session_state.year = current_year
            
            # Find default year index
            default_year_index = year_options.index(st.session_state.year)
            
            selected_year = st.selectbox(
                "Year",
                options=year_options,
                index=default_year_index,
                key='year_selector'
            )
            st.session_state.year = selected_year
            
        # Log current date and week information
        logging.info(f"Current date: {current_date}, Week number: {current_week}")

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
                
                # Show success message and mark form as submitted
                st.session_state.success_message = "✅ WPR updated successfully! Check your email for a summary."
                st.balloons()  # Add some celebration
                
                # Give time for success message and balloons
                time.sleep(1)
                
                # Rerun to refresh the page with cleared form
                st.rerun()
                
                # Reset edit mode
                st.session_state.edit_mode = False
                st.session_state.edit_id = None
                st.session_state.form_data = {}
                
        except Exception as e:
            logging.error(f"Error processing edit submission: {str(e)}")
            st.error("Error processing your submission. Please try again.")

    @handle_exceptions(error_types=(Exception,))
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
                member for member in self.config.TEAMS[team] 
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
            page_title=Constants.PAGE_TITLE,
            page_icon=Constants.PAGE_ICON,
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

    def process_submission(self, data: Dict[str, Any], user_email: str) -> bool:
        try:
            hr_analysis = None
            
            # Generate HR analysis if AI analyzer is available
            if self.ai_hr_analyzer:
                hr_analysis = self.ai_hr_analyzer.generate_hr_analysis(data)
                # Save HR analysis to database if generated
                if hr_analysis:
                    self.db.save_hr_analysis(hr_analysis)
            else:
                logging.warning("AI HR analysis skipped - analyzer not available")
            
            # Send email notification if handler is available, regardless of AI analysis
            if self.email_handler:
                ai_analysis = None
                if self.ai_hr_analyzer is not None:
                    try:
                        analysis_result = self.ai_hr_analyzer.generate_hr_analysis(data)
                        if analysis_result:
                            # Format AI analysis for email
                            performance_metrics = analysis_result.get('performance_metrics', {})
                            skill_assessment = analysis_result.get('skill_assessment', {})
                            wellness = analysis_result.get('wellness_indicators', {})
                            recommendations = analysis_result.get('growth_recommendations', {})
                            team_dynamics = analysis_result.get('team_dynamics', {})
                            
                            # Clean up the recommendations list
                            immediate_actions = recommendations.get('immediate_actions', [])
                            if isinstance(immediate_actions, str):
                                try:
                                    immediate_actions = eval(immediate_actions)
                                except:
                                    immediate_actions = [immediate_actions]
                            
                            # Format the date
                            current_date = datetime.now()
                            formatted_date = current_date.strftime("%B %d, %Y")
                            
                            ai_analysis = f"""Weekly Performance Analysis
Week {data['Week Number']} - {formatted_date}

Achievement Highlights
• Self-rated as "{data.get('Productivity Rating', 'N/A')}"
• Task Completion Rate: {performance_metrics.get('task_completion_rate', 0):.0f}% ({len(data.get('Completed Tasks', []))} completed, {len(data.get('Pending Tasks', []))} pending)
• Preferred Work Time: {data.get('Productive Time', 'Not specified')}
• Workplace Effectiveness: Shows preference for {data.get('Productive Place', 'various')} environment

Performance Metrics
• Task Management: {len(data.get('Completed Tasks', []))} tasks completed, {len(data.get('Pending Tasks', []))} pending
• Project Progress: {performance_metrics.get('project_progress', 0):.0f}% overall completion
• Collaboration Score: {performance_metrics.get('collaboration_score', 'N/A')} based on peer evaluations
• Productivity Rating: {performance_metrics.get('productivity_score', 'N/A')} out of 5

Growth Opportunities
"""
                            # Add technical skills if available
                            tech_skills = skill_assessment.get('technical_skills', [])
                            if tech_skills and isinstance(tech_skills, list):
                                ai_analysis += "• Technical Skills Development:\n"
                                for skill in tech_skills:
                                    if isinstance(skill, str):
                                        ai_analysis += f"  • {skill}\n"
                            
                            # Add soft skills if available
                            soft_skills = skill_assessment.get('soft_skills', [])
                            if soft_skills and isinstance(soft_skills, list):
                                ai_analysis += "• Soft Skills Enhancement:\n"
                                for skill in soft_skills:
                                    if isinstance(skill, str):
                                        ai_analysis += f"  • {skill}\n"
                            
                            ai_analysis += f"""
Action Plan"""
                            # Add recommendations
                            if immediate_actions and isinstance(immediate_actions, list):
                                for i, action in enumerate(immediate_actions, 1):
                                    if isinstance(action, str):
                                        ai_analysis += f"\n• {action}"
                            
                            ai_analysis += f"""

Team Collaboration
• Team Impact: {team_dynamics.get('team_impact', 'Continue fostering team collaboration')}
• Peer Feedback: {team_dynamics.get('peer_feedback_summary', 'Maintain open communication with team members')}

Wellness Check
• Workload Assessment: {wellness.get('workload_assessment', 'Balanced')}
• Engagement Level: {wellness.get('engagement_level', 'Good')}
• Work Environment: Effective utilization of {data.get('Productive Place', 'workspace')}
• Peak Productivity: Observed during {data.get('Productive Time', 'working hours')}

Generated by IOL HR Analysis System"""
                    except Exception as e:
                        logging.warning(f"Failed to generate HR analysis: {str(e)}")
                        ai_analysis = None
                
                success = self.email_handler.send_wpr_notification(
                    to_email=user_email,
                    to_name=data['Name'],
                    week_number=data['Week Number'],
                    year=data['Year'],
                    ai_analysis=ai_analysis
                )
                if not success:
                    st.warning("⚠️ Failed to send email notification. Please check the logs for details.")
            
            # Display HR analysis dashboard if analysis was generated
            # Removed HR dashboard display
            
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
                
                # Show success message and mark form as submitted
                st.session_state.success_message = "✅ WPR submitted successfully! Check your email for a summary."
                st.balloons()  # Add some celebration
                
                # Give time for success message and balloons
                time.sleep(1)
                
                # Rerun to refresh the page with cleared form
                st.rerun()
                
        except Exception as e:
            logging.error(f"Error processing form submission: {str(e)}")
            st.error("Error processing your submission. Please try again.")

    def run(self) -> None:
        """Run the WPR application"""
        try:
            self.setup_page()
            self.initialize_session_state()
            
            # Get current week number for header display
            current_date = datetime.now()  # Using the current date
            current_week = current_date.isocalendar()[1]
            logging.info(f"Current date: {current_date}, Week number: {current_week}")
            
            # Display header with current week
            self.ui.display_header(current_week)
            
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