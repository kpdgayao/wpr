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
        completed_tasks = st.text_area("Completed Tasks (one per line)")
        pending_tasks = st.text_area("Pending Tasks (one per line)")
        dropped_tasks = st.text_area("Dropped Tasks (one per line)")

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
    projects = st.text_area("Projects")

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
        value='3 - Productive',
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
    ])
    productivity_details = st.text_area("Please provide more details or examples")

    # Add input fields for time and place of productivity
    st.markdown('<div class="subsection-header">Time and Place of Productivity</div>', unsafe_allow_html=True)
    productive_time = st.radio("What time are you most productive last week?", ["8am - 12nn", "12nn - 4pm", "4pm - 8pm", "8pm - 12mn"])
    productive_place = st.radio("Where do you prefer to work based on your experience from last week?", ["Office", "Home"])

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

    peer_evaluations = st.multiselect("Select the teammates you worked with last week", teammates)
    peer_ratings = {}
    for peer in peer_evaluations:
        rating = st.select_slider(f"Rate {peer}", options=["1 (Poor)", "2 (Fair)", "3 (Satisfactory)", "4 (Excellent)"], key=f"peer_rating_{peer}")
        peer_ratings[peer] = int(rating.split(" ")[0])  # Extract the numeric rating

    # Convert peer ratings to a list of dictionaries
    peer_evaluations_list = [{"Peer": peer, "Rating": rating} for peer, rating in peer_ratings.items()]

    # Calculate the team overall rating
    if peer_ratings:
        team_overall_rating = sum(peer_ratings.values()) / len(peer_ratings)
        st.write(f"Team Overall Rating: {team_overall_rating:.2f}")
    else:
        st.write("No peer evaluations provided.")

    user_email = st.text_input("Enter your email address")      

    # Display the entered information and save data
    if st.button("Submit") and not st.session_state['submitted']:
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
        save_data(data)

        # Format the submission text based on the user's saved data
        submission_text = f"Name: {data['Name']}\nTeam: {data['Team']}\nWeek Number: {data['Week Number']}\nYear: {data['Year']}\n\nCompleted Tasks: {data['Completed Tasks']}\nNumber of Completed Tasks: {data['Number of Completed Tasks']}\n\nPending Tasks: {data['Pending Tasks']}\nNumber of Pending Tasks: {data['Number of Pending Tasks']}\n\nDropped Tasks: {data['Dropped Tasks']}\nNumber of Dropped Tasks: {data['Number of Dropped Tasks']}\n\nProjects: {data['Projects']}\n\n"

        # Add last week's pending tasks and projects if available
        if 'past_week_pending_tasks' in locals():
            submission_text += f"Last Week's Pending Tasks: {past_week_pending_tasks}\n"
        else:
            submission_text += "Last Week's Pending Tasks: Not available\n"

        if 'past_week_projects' in locals():
            submission_text += f"Last Week's Projects: {past_week_projects}\n"
        else:
            submission_text += "Last Week's Projects: Not available\n"

        submission_text += f"\nProductivity Rating: {data['Productivity Rating']}\nProductivity Suggestions: {data['Productivity Suggestions']}\nProductivity Details: {data['Productivity Details']}\nProductive Time: {data['Productive Time']}\nProductive Place: {data['Productive Place']}\n\nPeer Evaluations: {data['Peer_Evaluations']}"

       # Process the submission using Anthropic API
        anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]
        client = anthropic.Client(api_key=anthropic_api_key)

        # Define the system prompt
        system_prompt = """You are an HR productivity expert for IOL Inc., a systems development startup. Please summarize the following text from the Weekly Productivity Report and provide actionable insights, things-to-do checklist, recommendations, and motivation to the employee. Format your response as follows:

        <h2>Hello!</h2> 
        <h3>Summary:</h3>
        [Summary of the WPR submission]

        <h3>Insights and Recommendations:</h3>
        [Bullet points of insights and recommendations based on the WPR data]

        <h3>To-do List:</h3>
        [A list of pending tasks this week]

        <h3>Motivation:</h3>
        [A short motivational message for the employee]

        <h3>Weekly Productivity Tips:</h3>
        <ol>
        <li>[Practical tip 1]</li>
        <li>[Practical tip 2]</li>
        <li>[Practical tip 3]</li>
        </ol>

        <p><strong>Thanks from your IOL Team!</strong></p>

        Address the recipient in second person point of view and skip the preamble. Your response should be in HTML format."""

        # Define the user message
        user_message = f"Here is the text: \n\n{submission_text}"

        try:
            response = client.messages.create(
                model="claude-3-opus-20240229",
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                max_tokens=1024,
            )
            processed_output = response.content[0].text
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

        # Send the email using Mailjet API
        try:
            result = mailjet.send.create(data=email_data)
            print(f"Email sent with status code: {result.status_code}")
            st.success("Email sent successfully!")
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            st.error(f"An error occurred while sending the email: {str(e)}")

        st.session_state['submitted'] = True
        st.markdown('<div class="success-message">WPR submitted successfully! Check your email for a summary.</div>', unsafe_allow_html=True)

