import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
from datetime import datetime
from database import save_data, load_data, display_data
import pandas as pd
import matplotlib.pyplot as plt
from mailjet_rest import Client
import anthropic
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from .env file
load_dotenv()

# Retrieve Supabase URL and API key from environment variables
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# Initialize the Supabase client
supabase = create_client(url, key)

# Set page title and favicon
st.set_page_config(page_title="IOL Weekly Productivity Report", page_icon=":clipboard:")

# Define custom CSS styles
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

# Display custom CSS styles
st.markdown(custom_css, unsafe_allow_html=True)

# Display title and description
st.markdown('<div class="title">IOL Weekly Productivity Report (WPR)</div>', unsafe_allow_html=True)
st.write("Track and report your weekly productivity.")

# Initialize session state
if 'selected_name' not in st.session_state:
    st.session_state['selected_name'] = ""
if 'week_number' not in st.session_state:
    st.session_state['week_number'] = datetime.now().isocalendar()[1]
if 'show_task_section' not in st.session_state:
    st.session_state['show_task_section'] = False
if 'show_project_section' not in st.session_state:
    st.session_state['show_project_section'] = False
if 'show_productivity_section' not in st.session_state:
    st.session_state['show_productivity_section'] = False
if 'show_peer_evaluation_section' not in st.session_state:
    st.session_state['show_peer_evaluation_section'] = False
if 'submitted' not in st.session_state:
    st.session_state['submitted'] = False

# Initialize session state variables for storing user responses
if 'completed_tasks' not in st.session_state:
    st.session_state['completed_tasks'] = ""
if 'pending_tasks' not in st.session_state:
    st.session_state['pending_tasks'] = ""
if 'dropped_tasks' not in st.session_state:
    st.session_state['dropped_tasks'] = ""
if 'projects' not in st.session_state:
    st.session_state['projects'] = ""
if 'productivity_rating' not in st.session_state:
    st.session_state['productivity_rating'] = '3 - Productive'
if 'productivity_suggestions' not in st.session_state:
    st.session_state['productivity_suggestions'] = []
if 'productivity_details' not in st.session_state:
    st.session_state['productivity_details'] = ""
if 'productive_time' not in st.session_state:
    st.session_state['productive_time'] = "8am - 12nn"
if 'productive_place' not in st.session_state:
    st.session_state['productive_place'] = "Office"
if 'peer_evaluations' not in st.session_state:
    st.session_state['peer_evaluations'] = []

# Define the get_week_dates function
from datetime import datetime, timedelta

def get_week_dates(week_number, year):
    first_day_of_year = datetime(year, 1, 1)
    first_monday_of_year = first_day_of_year + timedelta(days=(7 - first_day_of_year.weekday()) % 7)
    selected_week_start = first_monday_of_year + timedelta(weeks=week_number - 1)
    selected_week_end = selected_week_start + timedelta(days=6)
    return selected_week_start.strftime("%B %d, %Y"), selected_week_end.strftime("%B %d, %Y")

# Define teams and their members
teams = {
    "Business Services Team": ["Abigail Visperas", "Cristian Jay Duque", "Kevin Philip Gayao", "Kurt Lee Gayao", "Maria Luisa Reynante", "Jester Pedrosa"],
    "Frontend Team": ["Amiel Bryan Gaudia", "George Libatique", "Joshua Aficial"],
    "Backend Team": ["Jeon Angelo Evangelista", "Katrina Gayao", "Renzo Ducusin"]
}

# Show current date today
current_date = datetime.now().strftime("%B %d, %Y")
st.write(f"Date Today: {current_date}")

# Create a list of names with team information
names = [f"{name} ({team})" for team, members in teams.items() for name in members]

# Add a selectbox with search functionality
selected_name = st.selectbox("Enter Your Name", [""] + names, format_func=lambda x: "Select a name" if x == "" else x, key="name_search")

# Update session state when a name is selected
if selected_name:
    st.session_state['selected_name'] = selected_name

# Get the current date and calculate the week number
current_date = datetime.now()
current_week = current_date.isocalendar()[1]
current_year = current_date.year

# Add an input field for the user to enter the week number
week_number = st.number_input("Enter the Week Number", min_value=1, max_value=52, value=st.session_state['week_number'], step=1)

# Update session state when the week number changes
if week_number != st.session_state['week_number']:
    st.session_state['week_number'] = week_number

# Display the entered week number and current year
st.write(f"Selected Week: Week {st.session_state['week_number']}, {current_year}")

# Add a button to proceed to the task section
if st.button("Proceed") and st.session_state['selected_name']:
    st.session_state['show_task_section'] = True

# Check if the user has already submitted a report for the selected week
user_data = load_data()
if not user_data.empty:
    user_submissions = user_data[(user_data["Name"] == st.session_state['selected_name']) & (user_data["Week Number"] == st.session_state['week_number'])]
    if not user_submissions.empty:
        st.warning("You have already submitted a report for this week.")
        st.session_state['submitted'] = True
        
        # Load the user's previous submission data
        previous_submission = user_submissions.iloc[0]
        st.session_state['completed_tasks'] = "\n".join(previous_submission["Completed Tasks"])
        st.session_state['pending_tasks'] = "\n".join(previous_submission["Pending Tasks"])
        st.session_state['dropped_tasks'] = "\n".join(previous_submission["Dropped Tasks"])
        st.session_state['projects'] = "\n".join([f"{project['name']}, {project['completion']}" for project in previous_submission["Projects"]])
        st.session_state['productivity_rating'] = previous_submission["Productivity Rating"]
        st.session_state['productivity_suggestions'] = previous_submission["Productivity Suggestions"]
        st.session_state['productivity_details'] = previous_submission["Productivity Details"]
        st.session_state['productive_time'] = previous_submission["Productive Time"]
        st.session_state['productive_place'] = previous_submission["Productive Place"]
        st.session_state['peer_evaluations'] = [peer['Peer'] for peer in previous_submission["Peer_Evaluations"]]
        # Add a checkbox to allow the user to edit their previous submission
        edit_mode = st.checkbox("Edit Previous Submission")
    else:
        st.session_state['submitted'] = False
        edit_mode = False
else:
    st.session_state['submitted'] = False
    edit_mode = False

    # Display the selected week's dates
    selected_week_start, selected_week_end = get_week_dates(st.session_state['week_number'], current_year)
    st.write(f"Selected Week: Week {st.session_state['week_number']}, {current_year}")
    st.write(f"Week Dates: {selected_week_start} - {selected_week_end}")

if st.session_state['show_task_section']:
    if st.session_state['selected_name'] in names:
        # Extract the team from the selected name
        team = st.session_state['selected_name'].split("(")[-1].split(")")[0]

        st.markdown(f'<div class="section-header">Welcome, {st.session_state["selected_name"].split("(")[0].strip()}</div>', unsafe_allow_html=True)
        st.write(f"Team: {team}")

        # Display the last 5 responses of the user
        st.markdown('<div class="section-header">Your Last 5 Responses</div>', unsafe_allow_html=True)
        user_data = load_data()

        if not user_data.empty and 'Name' in user_data.columns:
            user_responses = user_data[user_data["Name"] == st.session_state['selected_name']].sort_values("Week Number", ascending=False).head(5)
            
            if not user_responses.empty:
                # Create line charts for completed, pending, and dropped tasks
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(user_responses["Week Number"], user_responses["Number of Completed Tasks"], marker="o", label="Completed Tasks")
                ax.plot(user_responses["Week Number"], user_responses["Number of Pending Tasks"], marker="o", label="Pending Tasks")
                ax.plot(user_responses["Week Number"], user_responses["Number of Dropped Tasks"], marker="o", label="Dropped Tasks")
                ax.set_xlabel("Week Number")
                ax.set_ylabel("Number of Tasks")
                ax.set_title("Task Trends")
                ax.grid(True)
                ax.legend()
                st.pyplot(fig)

                # Display projects for the past week
                st.markdown('<div class="subsection-header">Projects for the Past Week</div>', unsafe_allow_html=True)
                past_week_projects = user_responses.iloc[0]["Projects"]
                if past_week_projects:
                    for project in past_week_projects:
                        st.write(f"{project['name']}: {project['completion']}%")
                else:
                    st.write("No projects found for the past week.")
                
                # Display pending tasks from the previous week
                st.markdown('<div class="subsection-header">Pending Tasks from Last Week</div>', unsafe_allow_html=True)
                past_week_pending_tasks = user_responses.iloc[0]["Pending Tasks"]
                if past_week_pending_tasks:
                    for task in past_week_pending_tasks:
                        st.write(f"- {task}")
                else:
                    st.write("No pending tasks from the previous week.")
        else:
            st.write("No previous responses found.")

        # Add input fields for task completion
        st.markdown('<div class="subsection-header">Task Completion</div>', unsafe_allow_html=True)
        completed_tasks = st.text_area("Completed Tasks (one per line)", value=st.session_state.get('completed_tasks', ''), key='completed_tasks')
        pending_tasks = st.text_area("Pending Tasks (one per line)", value=st.session_state.get('pending_tasks', ''), key='pending_tasks')
        dropped_tasks = st.text_area("Dropped Tasks (one per line)", value=st.session_state.get('dropped_tasks', ''), key='dropped_tasks')
       
        # Convert tasks to lists
        completed_tasks_list = completed_tasks.split("\n") if completed_tasks else []
        pending_tasks_list = pending_tasks.split("\n") if pending_tasks else []
        dropped_tasks_list = dropped_tasks.split("\n") if dropped_tasks else []

        # Calculate total tasks and percentages
        total_tasks = len(completed_tasks_list) + len(pending_tasks_list) + len(dropped_tasks_list)
        completed_percentage = (len(completed_tasks_list) / total_tasks) * 100 if total_tasks > 0 else 0
        pending_percentage = (len(pending_tasks_list) / total_tasks) * 100 if total_tasks > 0 else 0
        dropped_percentage = (len(dropped_tasks_list) / total_tasks) * 100 if total_tasks > 0 else 0

        # Display task summary
        st.markdown('<div class="subsection-header">Task Summary</div>', unsafe_allow_html=True)
        st.write(f"Total Tasks: {total_tasks}")
        st.write(f"Completed Tasks: {len(completed_tasks_list)} ({completed_percentage:.2f}%)")
        st.write(f"Pending Tasks: {len(pending_tasks_list)} ({pending_percentage:.2f}%)")
        st.write(f"Dropped Tasks: {len(dropped_tasks_list)} ({dropped_percentage:.2f}%)")

        # Add a button to proceed to the project section
        if st.button("Next", key='task_next'):
            st.session_state['show_project_section'] = True

    else:
        st.warning("Please select a valid name from the dropdown.")

if st.session_state['show_project_section']:
    # Add input fields for projects
    st.markdown('<div class="section-header">Projects</div>', unsafe_allow_html=True)
    st.write("Enter projects and their completion percentage (one per line, format: project name, completion percentage without '%' symbol)")
    projects = st.text_area("Projects", value=st.session_state.get('projects', ''), key='projects')

    # Convert projects to a list of dictionaries
    projects_list = []
    for project in projects.split("\n"):
        if project:
            try:
                name, completion = project.rsplit(",", maxsplit=1)
                completion = float(completion.strip())
                if completion < 0 or completion > 100:
                    raise ValueError("Completion percentage must be between 0 and 100")
                projects_list.append({"name": name.strip(), "completion": completion})
            except ValueError as e:
                st.error(f"Invalid project format: {project}. {str(e)}")

    # Add a button to proceed to the productivity section
    if st.button("Next", key='project_next'):
        st.session_state['show_productivity_section'] = True

if st.session_state['show_productivity_section']:
    # Add input fields for productivity evaluation
    st.markdown('<div class="section-header">Productivity Evaluation</div>', unsafe_allow_html=True)
    productivity_rating = st.select_slider(
        "Productivity Rating",
        options=['1 - Not Productive', '2 - Somewhat Productive', '3 - Productive', '4 - Very Productive'],
        value=st.session_state.get('productivity_rating', '3 - Productive'),
        key='productivity_rating'
    )
    productivity_suggestions = st.multiselect("Productivity Suggestions", [
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
    ], default=st.session_state.get('productivity_suggestions', []), key='productivity_suggestions')
    productivity_details = st.text_area("Please provide more details or examples", value=st.session_state.get('productivity_details', ''), key='productivity_details')

    # Add input fields for time and place of productivity
    st.markdown('<div class="subsection-header">Time and Place of Productivity</div>', unsafe_allow_html=True)
    productive_time = st.radio("What time are you most productive last week?", ["8am - 12nn", "12nn - 4pm", "4pm - 8pm", "8pm - 12mn"], index=["8am - 12nn", "12nn - 4pm", "4pm - 8pm", "8pm - 12mn"].index(st.session_state.get('productive_time', "8am - 12nn")), key='productive_time')
    productive_place = st.radio("Where do you prefer to work based on your experience from last week?", ["Office", "Home"], index=["Office", "Home"].index(st.session_state.get('productive_place', "Office")), key='productive_place')

    # Add a button to proceed to the peer evaluation section
    if st.button("Next", key='productivity_next'):
        st.session_state['show_peer_evaluation_section'] = True

if st.session_state['show_peer_evaluation_section']:
    # Add input fields for peer evaluation
    st.markdown('<div class="section-header">Peer Evaluation (Evaluate Your Teammates)</div>', unsafe_allow_html=True)
    st.write("Select the teammates you worked with last week and provide a rating for their performance.")

    # Get the selected user's team
    selected_team = st.session_state['selected_name'].split("(")[-1].split(")")[0]

    # Get the list of teammates for the selected user
    teammates = [name for name in names if selected_team in name and name != st.session_state['selected_name']]

    valid_peer_evaluations = [peer for peer in st.session_state.get('peer_evaluations', []) if peer in teammates]

    peer_evaluations = st.multiselect("Select the teammates you worked with last week", teammates, default=valid_peer_evaluations, key='peer_evaluations')

    peer_ratings = {}
    for peer in peer_evaluations:
        rating = st.radio(f"Rate {peer}", options=["1", "2", "3", "4"], key=f"peer_rating_{peer}")
        if rating:  # add a check if a rating was selected
            peer_ratings[peer] = int(rating)

    # Convert peer ratings to a list of dictionaries
    peer_evaluations_list = [{"Peer": peer, "Rating": peer_ratings.get(peer, 0)} for peer in peer_evaluations]

    # Calculate the team overall rating
    if peer_ratings:
        team_overall_rating = sum(peer_ratings.values()) / len(peer_ratings)
        st.write(f"Team Overall Rating: {team_overall_rating:.2f}")
    else:
        st.write("No peer evaluations provided.")

    user_email = st.text_input("Enter your email address")

# Display the entered information and save data
    if st.button("Submit"):
        # Get the selected week's dates
        selected_week_start, selected_week_end = get_week_dates(st.session_state['week_number'], current_year)
        
        data = {
            "Name": st.session_state['selected_name'],
            "Team": team,
            "Week Number": st.session_state['week_number'],
            "Year": current_year,
            "Completed Tasks": completed_tasks_list,
            "Number of Completed Tasks": len(completed_tasks_list),
            "Pending Tasks": pending_tasks_list,
            "Number of Pending Tasks": len(pending_tasks_list),
            "Dropped Tasks": dropped_tasks_list,
            "Number of Dropped Tasks": len(dropped_tasks_list),
            "Projects": projects_list,
            "Productivity Rating": productivity_rating,
            "Productivity Suggestions": productivity_suggestions,
            "Productivity Details": productivity_details,
            "Productive Time": productive_time,
            "Productive Place": productive_place,
            "Peer_Evaluations": peer_evaluations_list
        }
    
        # Display progress indicator while saving data
        with st.spinner("Saving data..."):
            if edit_mode:
                # Update the existing submission
                supabase.table("wpr_data").update(data).eq("Name", st.session_state['selected_name']).eq("Week Number", st.session_state['week_number']).execute()
            else:
                # Create a new submission
                supabase.table("wpr_data").insert(data).execute()
            
            st.success("Data saved successfully!")

        # **Updated code start**
        # Format the submission text based on the user's saved data
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
        """

        # Add last week's pending tasks and projects if available
        if 'past_week_pending_tasks' in locals():
            submission_text += f"Last Week's Pending Tasks: {past_week_pending_tasks}\n"
        else:
            submission_text += "Last Week's Pending Tasks: Not available\n"

        if 'past_week_projects' in locals():
            submission_text += f"Last Week's Projects: {past_week_projects}\n"
        else:
            submission_text += "Last Week's Projects: Not available\n"

        submission_text += f"""
    Productivity Rating: {data['Productivity Rating']}
    Productivity Suggestions: {data['Productivity Suggestions']}
    Productivity Details: {data['Productivity Details']}
    Productive Time: {data['Productive Time']}
    Productive Place: {data['Productive Place']}

    Peer Evaluations: {data['Peer_Evaluations']}
    """
    # **Updated code end**
       # Process the submission using Anthropic API
        anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]
        client = anthropic.Client(api_key=anthropic_api_key)

        # Define the system prompt
        system_prompt = f"""You are an HR productivity expert for IOL Inc., a systems development startup. Please summarize the following text from the Weekly Productivity Report for Week {st.session_state['week_number']} ({selected_week_start} - {selected_week_end}) and provide actionable insights, a to-do checklist, recommendations, and motivation to the employee. 

        The report includes the employee's completed tasks, pending tasks, dropped tasks, projects, productivity self-evaluation, and peer evaluations provided by the employee as the evaluator.

        Format your response as follows:

        <h2>Hello, [Employee Name]!</h2>

        <h3>Summary:</h3>
        [Provide a brief summary of the employee's productivity based on their completed tasks, pending tasks, dropped tasks, and projects for Week {st.session_state['week_number']} ({selected_week_start} - {selected_week_end}).]

        <h3>Insights and Recommendations:</h3>
        [Offer insights and recommendations based on the employee's productivity data and self-evaluation for Week {st.session_state['week_number']}. Highlight areas of strength and suggest areas for improvement.]

        <h3>To-do List:</h3>
        [Create a to-do list for the employee based on their pending tasks and projects for the upcoming week. Prioritize tasks and provide guidance on how to approach them effectively.]

        <h3>Peer Feedback:</h3>
        [Summarize how the employee evaluated his or her peers for Week {st.session_state['week_number']}. Employee has rated his or her peers from 1 to 4, with 1 being the lowest and 4 highest. Offer insights on how the employee can contribute to team collaboration and support the employee's teammates.]

        <h3>Motivation:</h3>
        [Provide a motivational message to encourage the employee to maintain or improve their productivity for the upcoming week. Recognize their efforts and achievements from Week {st.session_state['week_number']}.]

        <h3>Weekly Productivity Tips:</h3>
        <ol>
        <li>[Offer a practical tip to enhance productivity based on the employee's self-evaluation and productivity data for Week {st.session_state['week_number']}.]</li>
        <li>[Provide another tip to help the employee manage their tasks and projects effectively in the upcoming week.]</li>
        <li>[Suggest a strategy to maintain work-life balance and prevent burnout.]</li>
        </ol>

        <p><strong>Keep up the great work, [Employee Name]! Your contributions are valued and appreciated.</strong></p>

        <p>Best regards,<br>
        The IOL Inc. Team</p>

        Address the recipient in the second person point of view and skip the preamble. Your response should be in HTML format."""

        # Define the user message
        user_message = f"Here is the text: \n\n{submission_text}"

        # Display progress indicator while processing the submission
        with st.spinner("Processing submission..."):
            try:
                response = client.messages.create(
                    model="claude-3-sonnet-20240229",
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_message}],
                    max_tokens=2000,
                )
                processed_output = response.content[0].text
                st.success("Submission processed successfully!")
            except anthropic.APIError as e:
                processed_output = f"Error occurred while processing the request. Please try again later. Error details: {str(e)}"
                st.error(f"Error occurred while processing the request. Please try again later. Error details: {str(e)}")
            except Exception as e:
                processed_output = f"An unexpected error occurred. Please try again later. Error details: {str(e)}"
                st.error(f"An unexpected error occurred. Please try again later. Error details: {str(e)}")

        # Mailjet API credentials
        api_key = os.environ['MAILJET_API_KEY']
        api_secret = os.environ['MAILJET_API_SECRET']

        # Create a Mailjet client
        mailjet = Client(auth=(api_key, api_secret), version='v3.1')

        # Prepare the email data
        email_data = {
            'Messages': [
                {
                    "From": {
                        "Email": "go@iol.ph",
                        "Name": "IOL Inc."
                    },
                    "To": [
                        {
                            "Email": user_email,
                            "Name": st.session_state['selected_name']
                        }
                    ],
                    "Subject": "Weekly Productivity Report Summary",
                    "HTMLPart": processed_output
                }
            ]
        }

        # Display progress indicator while sending the email
        with st.spinner("Sending email..."):
            try:
                result = mailjet.send.create(data=email_data)
                print(f"Email sent with status code: {result.status_code}")
                st.success("Email sent successfully!")
            except Exception as e:
                print(f"Error sending email: {str(e)}")
                st.error(f"An error occurred while sending the email: {str(e)}")

        st.session_state['submitted'] = True
        st.markdown('<div class="success-message">WPR submitted successfully! Check your email for a summary.</div>', unsafe_allow_html=True)

