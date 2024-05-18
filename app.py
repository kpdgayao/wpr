import streamlit as st
from datetime import datetime
from database import save_data, load_data, display_data
import pandas as pd
import matplotlib.pyplot as plt

# Set page title and favicon
st.set_page_config(page_title="Weekly Progress Report", page_icon=":clipboard:")

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
st.markdown('<div class="title">Weekly Progress Report (WPR)</div>', unsafe_allow_html=True)
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

# Define teams and their members
teams = {
    "Business Services Team": ["Abigail Visperas", "Cristian Jay Duque", "Kevin Philip Gayao", "Kurt Lee Gayao", "Maria Luisa Reynante", "Jester Pedrosa"],
    "Frontend Team": ["Amiel Bryan Gaudia", "George Libatique", "Joshua Aficial"],
    "Backend Team": ["Jeon Angelo Evangelista", "Katrina Gayao", "Renzo Ducusin"]
}

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
        else:
            st.write("No previous responses found.")

        # Add input fields for task completion
        st.markdown('<div class="subsection-header">Task Completion</div>', unsafe_allow_html=True)
        num_completed_tasks = st.number_input("Number of Completed Tasks", min_value=0, step=1, value=0)
        completed_tasks = []
        if num_completed_tasks > 0:
            for i in range(int(num_completed_tasks)):
                task = st.text_input(f"Completed Task {i+1}", key=f"completed_task_{i}")
                completed_tasks.append(task)
        else:
            no_completed_tasks = st.checkbox("No Completed Tasks", value=True)

        num_pending_tasks = st.number_input("Number of Pending Tasks", min_value=0, step=1, value=0)
        pending_tasks = []
        if num_pending_tasks > 0:
            for i in range(int(num_pending_tasks)):
                task = st.text_input(f"Pending Task {i+1}", key=f"pending_task_{i}")
                pending_tasks.append(task)
        else:
            no_pending_tasks = st.checkbox("No Pending Tasks", value=True)

        num_dropped_tasks = st.number_input("Number of Dropped Tasks", min_value=0, step=1, value=0)
        dropped_tasks = []
        if num_dropped_tasks > 0:
            for i in range(int(num_dropped_tasks)):
                task = st.text_input(f"Dropped Task {i+1}", key=f"dropped_task_{i}")
                dropped_tasks.append(task)
        else:
            no_dropped_tasks = st.checkbox("No Dropped Tasks", value=True)

        # Calculate total tasks and percentages
        total_tasks = num_completed_tasks + num_pending_tasks + num_dropped_tasks
        completed_percentage = (num_completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        pending_percentage = (num_pending_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        dropped_percentage = (num_dropped_tasks / total_tasks) * 100 if total_tasks > 0 else 0

        # Display task summary
        st.markdown('<div class="subsection-header">Task Summary</div>', unsafe_allow_html=True)
        st.write(f"Total Tasks: {total_tasks}")
        st.write(f"Completed Tasks: {num_completed_tasks} ({completed_percentage:.2f}%)")
        st.write(f"Pending Tasks: {num_pending_tasks} ({pending_percentage:.2f}%)")
        st.write(f"Dropped Tasks: {num_dropped_tasks} ({dropped_percentage:.2f}%)")

        # Add a button to proceed to the project section
        if st.button("Next", key='task_next'):
            st.session_state['show_project_section'] = True

    else:
        st.warning("Please select a valid name from the dropdown.")

if st.session_state['show_project_section']:
    # Add input fields for projects
    st.markdown('<div class="section-header">Projects</div>', unsafe_allow_html=True)
    num_projects = st.number_input("Number of Projects", min_value=0, step=1, value=0)
    projects = []
    if num_projects > 0:
        for i in range(int(num_projects)):
            project_name = st.text_input(f"Project {i+1} Name", key=f"project_name_{i}")
            project_completion = st.number_input(f"Project {i+1} Completion (%)", min_value=0, max_value=100, step=1, key=f"project_completion_{i}")
            projects.append({"name": project_name, "completion": project_completion})
    else:
        no_projects = st.checkbox("No Projects", value=True)

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
        "More Tools",
        "More Supervision",
        "Scheduled Breaks",
        "Monetary Incentives",
        "Better Time Management",
        "Improved Communication",
        "Alignment Meetings",
        "Collaborative Activities",
        "Training and Development",
        "Workload Balancing"
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
    st.markdown('<div class="section-header">Peer Evaluation</div>', unsafe_allow_html=True)

    # Get the selected user's team
    selected_team = st.session_state['selected_name'].split("(")[-1].split(")")[0]

    # Get the list of teammates for the selected user
    teammates = [name for name in names if selected_team in name and name != st.session_state['selected_name']]

    peer_evaluations = st.multiselect("Select the teammates you worked with last week", teammates)
    peer_ratings = {}
    for peer in peer_evaluations:
        rating = st.select_slider(f"Rate {peer}", options=["1 (Poor)", "2 (Fair)", "3 (Satisfactory)", "4 (Excellent)"], key=f"peer_rating_{peer}")
        peer_ratings[peer] = int(rating.split(" ")[0])  # Extract the numeric rating

    # Calculate the team overall rating
    if peer_ratings:
        team_overall_rating = sum(peer_ratings.values()) / len(peer_ratings)
        st.write(f"Team Overall Rating: {team_overall_rating:.2f}")
    else:
        st.write("No peer evaluations provided.")

    # Display the entered information and save data
    if st.button("Submit"):
        data = {
            "Name": st.session_state['selected_name'],
            "Team": team,
            "Week Number": st.session_state['week_number'],
            "Year": current_year,
            "Completed Tasks": completed_tasks,
            "Number of Completed Tasks": num_completed_tasks,
            "Pending Tasks": pending_tasks,
            "Number of Pending Tasks": num_pending_tasks,
            "Dropped Tasks": dropped_tasks,
            "Number of Dropped Tasks": num_dropped_tasks,
            "Projects": projects if num_projects > 0 else [],
            "Productivity Rating": productivity_rating,
            "Productivity Suggestions": productivity_suggestions,
            "Productivity Details": productivity_details,
            "Productive Time": productive_time,
            "Productive Place": productive_place,
            "Peer Ratings": list(peer_ratings.values())
        }
        save_data(data)
        st.markdown('<div class="success-message">WPR submitted successfully!</div>', unsafe_allow_html=True)