import os
import logging
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
from datetime import datetime, timedelta
from database import save_data, load_data, display_data
import pandas as pd
import matplotlib.pyplot as plt
from mailjet_rest import Client
import anthropic
from dotenv import load_dotenv
from supabase import create_client

# First Streamlit command - Page Configuration
st.set_page_config(page_title="IOL Weekly Productivity Report", page_icon=":clipboard:")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Config:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.mailjet_api_key = os.getenv("MAILJET_API_KEY")
        self.mailjet_api_secret = os.getenv("MAILJET_API_SECRET")
        
        # Teams configuration
        self.teams = {
            "Business Services Team": ["Abigail Visperas", "Cristian Jay Duque", "Justine Louise Ferrer", 
                                    "Nathalie Joy Fronda", "Kevin Philip Gayao", "Kurt Lee Gayao", 
                                    "Maria Luisa Reynante", "Jester Pedrosa"],
            "Frontend Team": ["Amiel Bryan Gaudia", "George Libatique", "Joshua Aficial"],
            "Backend Team": ["Jeon Angelo Evangelista", "Katrina Gayao", "Renzo Ducusin"]
        }
        
        # Productivity suggestions
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

class EmailHandler:
    def __init__(self, api_key, api_secret):
        self.client = Client(auth=(api_key, api_secret), version='v3.1')
    
    def send_email(self, to_email, to_name, subject, html_content):
        try:
            email_data = {
                'Messages': [{
                    "From": {"Email": "go@iol.ph", "Name": "IOL Inc."},
                    "To": [{"Email": to_email, "Name": to_name}],
                    "Subject": subject,
                    "HTMLPart": html_content
                }]
            }
            result = self.client.send.create(data=email_data)
            logging.info(f"Email sent successfully to {to_email}")
            return result
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            raise

class AIProcessor:
    def __init__(self, api_key):
        self.client = anthropic.Client(api_key=api_key)
    
    def process_submission(self, submission_text, system_prompt):
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                system=system_prompt,
                messages=[{"role": "user", "content": submission_text}],
                max_tokens=2000
            )
            return response.content[0].text
        except Exception as e:
            logging.error(f"AI processing error: {str(e)}")
            raise

@st.cache_data
def get_week_dates(week_number, year):
    first_day_of_year = datetime(year, 1, 1)
    first_monday_of_year = first_day_of_year + timedelta(days=(7 - first_day_of_year.weekday()) % 7)
    selected_week_start = first_monday_of_year + timedelta(weeks=week_number - 1)
    selected_week_end = selected_week_start + timedelta(days=6)
    return selected_week_start.strftime("%B %d, %Y"), selected_week_end.strftime("%B %d, %Y")

# Initialize configuration
config = Config()
email_handler = EmailHandler(config.mailjet_api_key, config.mailjet_api_secret)
supabase = create_client(config.supabase_url, config.supabase_key)

class UISetup:
    @staticmethod
    def load_custom_css():
        custom_css = """
            <style>
                .title {
                    font-size: 36px;
                    font-weight: bold;
                    color: #2E86C1;
                    margin-bottom: 20px;
                }
                .section-header {
                    font-size: 24px;
                    font-weight: bold;
                    color: #2E86C1;
                    margin-top: 40px;
                    margin-bottom: 20px;
                }
                .subsection-header {
                    font-size: 20px;
                    font-weight: bold;
                    color: #2E86C1;
                    margin-top: 30px;
                    margin-bottom: 10px;
                }
                .success-message {
                    font-size: 18px;
                    font-weight: bold;
                    color: #28B463;
                    margin-top: 20px;
                }
            </style>
        """
        st.markdown(custom_css, unsafe_allow_html=True)

    @staticmethod
    def initialize_session_state():
        # Basic session state variables
        session_vars = {
            'selected_name': "",
            'week_number': datetime.now().isocalendar()[1],
            'show_task_section': False,
            'show_project_section': False,
            'show_productivity_section': False,
            'show_peer_evaluation_section': False,
            'submitted': False
        }

        # Form data session state variables
        form_vars = {
            'completed_tasks': "",
            'pending_tasks': "",
            'dropped_tasks': "",
            'projects': "",
            'productivity_rating': '3 - Productive',
            'productivity_suggestions': [],
            'productivity_details': "",
            'productive_time': "8am - 12nn",
            'productive_place': "Office",
            'peer_evaluations': []
        }

        # Initialize all session state variables
        for var, default_value in {**session_vars, **form_vars}.items():
            if var not in st.session_state:
                st.session_state[var] = default_value

    @staticmethod
    def setup_page():
        st.markdown('<div class="title">IOL Weekly Productivity Report (WPR)</div>', unsafe_allow_html=True)
        st.write("Track and report your weekly productivity.")

class DataValidator:
    @staticmethod
    def validate_email(email):
        import re
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(pattern, email):
            raise ValueError("Invalid email format")
        return True

    @staticmethod
    def validate_tasks(tasks_list):
        if not isinstance(tasks_list, list):
            raise ValueError("Tasks must be a list")
        return all(isinstance(task, str) and task.strip() for task in tasks_list)

    @staticmethod
    def validate_projects(projects_list):
        if not isinstance(projects_list, list):
            raise ValueError("Projects must be a list")
        for project in projects_list:
            if not isinstance(project, dict):
                raise ValueError("Each project must be a dictionary")
            if 'name' not in project or 'completion' not in project:
                raise ValueError("Project must have name and completion percentage")
            if not isinstance(project['completion'], (int, float)):
                raise ValueError("Completion percentage must be a number")
            if project['completion'] < 0 or project['completion'] > 100:
                raise ValueError("Completion percentage must be between 0 and 100")
        return True

# Initialize UI and validator
ui = UISetup()
ui.load_custom_css()
ui.initialize_session_state()
ui.setup_page()
validator = DataValidator()

class WPRApp:
    def __init__(self, config):
        self.config = config
        self.names = [f"{name} ({team})" for team, members in config.teams.items() for name in members]
        self.current_date = datetime.now()
        self.current_week = self.current_date.isocalendar()[1]
        self.current_year = self.current_date.year

    def display_header(self):
        current_date = self.current_date.strftime("%B %d, %Y")
        st.write(f"Date Today: {current_date}")

        # Name selection
        selected_name = st.selectbox(
            "Enter Your Name",
            [""] + self.names,
            format_func=lambda x: "Select a name" if x == "" else x,
            key="name_search"
        )
        if selected_name:
            st.session_state['selected_name'] = selected_name

        # Week selection
        week_number = st.number_input(
            "Enter the Week Number",
            min_value=1,
            max_value=52,
            value=st.session_state['week_number'],
            step=1
        )
        if week_number != st.session_state['week_number']:
            st.session_state['week_number'] = week_number

        # Display week dates
        selected_week_start, selected_week_end = get_week_dates(week_number, self.current_year)
        st.write(f"Selected Week: Week {week_number}, {self.current_year}")
        st.write(f"Week Dates: {selected_week_start} - {selected_week_end}")

    def check_existing_submission(self):
        user_data = load_data()
        if not user_data.empty:
            user_submissions = user_data[
                (user_data["Name"] == st.session_state['selected_name']) & 
                (user_data["Week Number"] == st.session_state['week_number'])
            ]
            if not user_submissions.empty:
                st.warning("You have already submitted a report for this week.")
                return True, user_submissions.iloc[0]
        return False, None

    @staticmethod
    def display_task_summary(completed_tasks_list, pending_tasks_list, dropped_tasks_list):
        total_tasks = len(completed_tasks_list) + len(pending_tasks_list) + len(dropped_tasks_list)
        if total_tasks > 0:
            completed_percentage = (len(completed_tasks_list) / total_tasks) * 100
            pending_percentage = (len(pending_tasks_list) / total_tasks) * 100
            dropped_percentage = (len(dropped_tasks_list) / total_tasks) * 100

            st.markdown('<div class="subsection-header">Task Summary</div>', unsafe_allow_html=True)
            st.write(f"Total Tasks: {total_tasks}")
            st.write(f"Completed Tasks: {len(completed_tasks_list)} ({completed_percentage:.2f}%)")
            st.write(f"Pending Tasks: {len(pending_tasks_list)} ({pending_percentage:.2f}%)")
            st.write(f"Dropped Tasks: {len(dropped_tasks_list)} ({dropped_percentage:.2f}%)")

# Initialize the WPR application
app = WPRApp(config)

# Display the header
app.display_header()

class SubmissionProcessor:
    def __init__(self, config, email_handler):
        self.config = config
        self.email_handler = email_handler
        self.anthropic_client = anthropic.Client(api_key=st.secrets["ANTHROPIC_API_KEY"])

    def prepare_submission_text(self, data, selected_week_start, selected_week_end):
        submission_text = f"""Name: {data['Name']}
        Team: {data['Team']}
        Week Number: {data['Week Number']}
        Week Dates: {selected_week_start} - {selected_week_end}
        Year: {data['Year']}
        
        Completed Tasks: {data['Completed Tasks']}
        Number of Completed Tasks: {data['Number of Completed Tasks']}
        
        Pending Tasks: {data['Pending Tasks']}
        Number of Pending Tasks: {data['Number of Pending Tasks']}
        
        Dropped Tasks: {data['Dropped Tasks']}
        Number of Dropped Tasks: {data['Number of Dropped Tasks']}
        
        Projects: {data['Projects']}
        
        Productivity Rating: {data['Productivity Rating']}
        Productivity Suggestions: {data['Productivity Suggestions']}
        Productivity Details: {data['Productivity Details']}
        Productive Time: {data['Productive Time']}
        Productive Place: {data['Productive Place']}

        Peer Evaluations: {data['Peer_Evaluations']}
        """
        return submission_text

    def get_system_prompt(self, week_number, selected_week_start, selected_week_end):
        return f"""You are an empathetic HR productivity expert and career coach for IOL Inc., a dynamic systems development startup. Analyze the following Weekly Productivity Report for Week {week_number} ({selected_week_start} - {selected_week_end}) and provide a comprehensive, encouraging, and actionable assessment.

                The report encompasses the employee's task completion metrics, project progress, self-evaluation of productivity, and peer evaluations where they acted as the evaluator. Your response should balance performance monitoring with personal growth and team development.

                Format your response using this structured, motivational framework:

                <h2>Hello, [Employee Name]! 👋</h2>

                <h3>Weekly Achievement Spotlight 🌟</h3>
                [Provide an encouraging summary of the employee's productivity, highlighting:
                - Task completion rate and efficiency
                - Project milestones reached
                - Notable accomplishments from Week {week_number}
                - Progress compared to previous weeks (if data available)
                Frame this as a celebration of their efforts while acknowledging challenges.]

                <h3>Growth Insights & Strategic Recommendations 📈</h3>
                [Offer detailed insights and actionable recommendations:
                - Analyze productivity patterns and highlight strengths
                - Identify growth opportunities in a constructive manner
                - Suggest specific strategies for task and project management
                - Address any productivity challenges mentioned in their self-evaluation
                - Connect recommendations to their stated productivity preferences (time and place)]

                <h3>Priority Action Plan for Next Week ✅</h3>
                [Create a structured, prioritized action plan:
                1. High-Priority Tasks (Must complete)
                2. Medium-Priority Tasks (Should complete)
                3. Lower-Priority Tasks (Nice to complete)
                Include specific approaches for each priority level and estimated time frames.]

                <h3>Team Collaboration Impact 🤝</h3>
                [Analyze their peer evaluations (scale 1-4) to:
                - Highlight their role in team dynamics
                - Suggest ways to enhance team collaboration
                - Provide specific strategies for supporting teammates
                - Recommend opportunities for knowledge sharing and mentoring
                Frame this in terms of both individual and team growth.]

                <h3>Motivation & Recognition 🏆</h3>
                [Craft a personalized motivational message that:
                - Acknowledges specific achievements from Week {week_number}
                - Connects their work to IOL's mission and growth
                - Recognizes their unique contributions and potential
                - Encourages resilience in facing challenges]

                <h3>Success Strategies for Week {week_number + 1} 💡</h3>
                <ol>
                <li><strong>Productivity Enhancement:</strong> [Offer a customized productivity tip based on their self-evaluation and work patterns]</li>
                <li><strong>Task Management:</strong> [Provide a specific strategy for handling their current task load and project commitments]</li>
                <li><strong>Work-Life Harmony:</strong> [Suggest a practical approach for maintaining balance, considering their preferred productive hours and work location]</li>
                <li><strong>Professional Development:</strong> [Recommend a specific skill-building or learning opportunity related to their current projects]</li>
                <li><strong>Team Building:</strong> [Suggest a concrete way to strengthen team relationships and collaboration]</li>
                </ol>

                <h3>Resource Recommendations 📚</h3>
                [Based on their productivity suggestions and challenges, recommend:
                - Specific tools or resources that could help
                - Relevant training opportunities
                - Potential mentorship connections
                - Team collaboration strategies]

                <p><strong>🌟 Keep shining, [Employee Name]! Your dedication to growth and contribution to IOL Inc. make a real difference. We're here to support your success every step of the way! 🚀</strong></p>

                <p>Best regards,<br>
                The IOL Inc. Team</p>

                Remember to maintain an encouraging and constructive tone throughout, focusing on growth and improvement while acknowledging both achievements and challenges."""

    def process_submission(self, data, user_email):
        try:
            # Get week dates
            selected_week_start, selected_week_end = get_week_dates(data['Week Number'], data['Year'])
            
            # Prepare submission text and system prompt
            submission_text = self.prepare_submission_text(data, selected_week_start, selected_week_end)
            system_prompt = self.get_system_prompt(data['Week Number'], selected_week_start, selected_week_end)

            # Process with Anthropic
            with st.spinner("Processing submission..."):
                try:
                    response = self.anthropic_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        system=system_prompt,
                        messages=[{"role": "user", "content": submission_text}],
                        max_tokens=2000
                    )
                    processed_output = response.content[0].text
                    st.success("Submission processed successfully!")
                except Exception as e:
                    logging.error(f"AI processing error: {str(e)}")
                    st.error("Error processing submission. Please try again.")
                    return False

            # Send email
            with st.spinner("Sending email..."):
                try:
                    self.email_handler.send_email(
                        to_email=user_email,
                        to_name=data['Name'],
                        subject="Weekly Productivity Report Summary",
                        html_content=processed_output
                    )
                    st.success("Email sent successfully!")
                except Exception as e:
                    logging.error(f"Email error: {str(e)}")
                    st.error("Error sending email. Please try again.")
                    return False

            return True

        except Exception as e:
            logging.error(f"Submission processing error: {str(e)}")
            st.error("An unexpected error occurred. Please try again.")
            return False

# Initialize the submission processor
submission_processor = SubmissionProcessor(config, email_handler)

# Main form handling and submission logic
if st.session_state['show_peer_evaluation_section']:
    # Your existing peer evaluation code here...
    user_email = st.text_input("Enter your email address")      

    # Display the entered information and save data
    if st.button("Submit") and not st.session_state['submitted']:
        if not user_email:
            st.error("Please enter your email address")
        else:
            try:
                validator.validate_email(user_email)
                # Prepare your data dictionary here
                data = {
                    "Name": st.session_state['selected_name'],
                    "Team": st.session_state['selected_name'].split("(")[1].split(")")[0],
                    "Week Number": st.session_state['week_number'],
                    "Year": datetime.now().year,
                    "Completed Tasks": st.session_state['completed_tasks'].split('\n') if st.session_state['completed_tasks'] else [],
                    "Number of Completed Tasks": len(st.session_state['completed_tasks'].split('\n')) if st.session_state['completed_tasks'] else 0,
                    "Pending Tasks": st.session_state['pending_tasks'].split('\n') if st.session_state['pending_tasks'] else [],
                    "Number of Pending Tasks": len(st.session_state['pending_tasks'].split('\n')) if st.session_state['pending_tasks'] else 0,
                    "Dropped Tasks": st.session_state['dropped_tasks'].split('\n') if st.session_state['dropped_tasks'] else [],
                    "Number of Dropped Tasks": len(st.session_state['dropped_tasks'].split('\n')) if st.session_state['dropped_tasks'] else 0,
                    "Projects": st.session_state['projects'],
                    "Productivity Rating": st.session_state['productivity_rating'],
                    "Productivity Suggestions": st.session_state['productivity_suggestions'],
                    "Productivity Details": st.session_state['productivity_details'],
                    "Productive Time": st.session_state['productive_time'],
                    "Productive Place": st.session_state['productive_place'],
                    "Peer_Evaluations": st.session_state['peer_evaluations']
                }
        
                with st.spinner("Processing your submission..."):
                    if submission_processor.process_submission(data, user_email):
                        st.session_state['submitted'] = True
                        st.markdown(
                            '<div class="success-message">WPR submitted successfully! Check your email for a summary.</div>',
                            unsafe_allow_html=True
                        )
            except ValueError as e:
                st.error(str(e))