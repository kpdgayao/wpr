import streamlit as st
from database import load_data, display_data
import matplotlib.pyplot as plt
import pandas as pd

# Set page configuration
st.set_page_config(page_title="CEO Dashboard", page_icon=":bar_chart:", layout="wide")

st.markdown("""
    <style>
    body {
        background-color: #f0f0f0;
    }
    .streamlit-expanderHeader {
        font-size: 18px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_cached_data():
    return load_data()

data = load_cached_data()

try:
    data["Week Number"] = pd.to_numeric(data["Week Number"], errors="coerce")
    data = data[data["Week Number"].notna()]
except KeyError:
    st.error("The 'Week Number' column is missing in the data.")
    data["Week Number"] = pd.Series(dtype=int)

try:
    data["Number of Completed Tasks"] = pd.to_numeric(data["Number of Completed Tasks"], errors="coerce")
    data["Number of Pending Tasks"] = pd.to_numeric(data["Number of Pending Tasks"], errors="coerce")
    data["Number of Dropped Tasks"] = pd.to_numeric(data["Number of Dropped Tasks"], errors="coerce")
    data = data[data[["Number of Completed Tasks", "Number of Pending Tasks", "Number of Dropped Tasks"]].notna().all(axis=1)]
except KeyError as e:
    st.error(f"The following column is missing in the data: {str(e)}")
    data["Number of Completed Tasks"] = pd.Series(dtype=int)
    data["Number of Pending Tasks"] = pd.Series(dtype=int)
    data["Number of Dropped Tasks"] = pd.Series(dtype=int)

# Convert "Productivity Rating" column to numeric
try:
    data["Productivity Rating"] = pd.to_numeric(data["Productivity Rating"].str.split(" - ").str[0], errors="coerce")
    data = data[data["Productivity Rating"].notna()]
except KeyError:
    st.error("The 'Productivity Rating' column is missing in the data.")
    data["Productivity Rating"] = pd.Series(dtype=float)

# Sidebar filters
st.sidebar.header("Filters")
selected_teams = st.sidebar.multiselect("Select Teams", data["Team"].unique(), default=data["Team"].unique())
selected_weeks = st.sidebar.multiselect("Select Week Numbers", data["Week Number"].unique(), default=data["Week Number"].unique())
selected_employees = st.sidebar.multiselect("Select Employees", data["Name"].unique(), default=data["Name"].unique())
selected_projects = st.sidebar.multiselect("Select Projects", data["Projects"].apply(lambda x: [project["name"] for project in x if isinstance(project, dict)]).explode().unique())

# Filter data based on selected team and week
@st.cache_data(show_spinner=False)
def filter_data(data, selected_teams, selected_weeks, selected_employees, selected_projects):
    if selected_teams and selected_weeks and selected_employees and selected_projects:
        filtered_data = data[(data["Team"].isin(selected_teams)) & (data["Week Number"].isin(selected_weeks)) & (data["Name"].isin(selected_employees)) & (data["Projects"].apply(lambda x: any(project["name"] in selected_projects for project in x if isinstance(project, dict))))]
    elif selected_teams and selected_weeks and selected_employees:
        filtered_data = data[(data["Team"].isin(selected_teams)) & (data["Week Number"].isin(selected_weeks)) & (data["Name"].isin(selected_employees))]
    elif selected_teams and selected_weeks and selected_projects:
        filtered_data = data[(data["Team"].isin(selected_teams)) & (data["Week Number"].isin(selected_weeks)) & (data["Projects"].apply(lambda x: any(project["name"] in selected_projects for project in x if isinstance(project, dict))))]
    elif selected_teams and selected_employees and selected_projects:
        filtered_data = data[(data["Team"].isin(selected_teams)) & (data["Name"].isin(selected_employees)) & (data["Projects"].apply(lambda x: any(project["name"] in selected_projects for project in x if isinstance(project, dict))))]
    elif selected_weeks and selected_employees and selected_projects:
        filtered_data = data[(data["Week Number"].isin(selected_weeks)) & (data["Name"].isin(selected_employees)) & (data["Projects"].apply(lambda x: any(project["name"] in selected_projects for project in x if isinstance(project, dict))))]
    elif selected_teams and selected_weeks:
        filtered_data = data[(data["Team"].isin(selected_teams)) & (data["Week Number"].isin(selected_weeks))]
    elif selected_teams and selected_employees:
        filtered_data = data[(data["Team"].isin(selected_teams)) & (data["Name"].isin(selected_employees))]
    elif selected_teams and selected_projects:
        filtered_data = data[(data["Team"].isin(selected_teams)) & (data["Projects"].apply(lambda x: any(project["name"] in selected_projects for project in x if isinstance(project, dict))))]
    elif selected_weeks and selected_employees:
        filtered_data = data[(data["Week Number"].isin(selected_weeks)) & (data["Name"].isin(selected_employees))]
    elif selected_weeks and selected_projects:
        filtered_data = data[(data["Week Number"].isin(selected_weeks)) & (data["Projects"].apply(lambda x: any(project["name"] in selected_projects for project in x if isinstance(project, dict))))]
    elif selected_employees and selected_projects:
        filtered_data = data[(data["Name"].isin(selected_employees)) & (data["Projects"].apply(lambda x: any(project["name"] in selected_projects for project in x if isinstance(project, dict))))]
    elif selected_teams:
        filtered_data = data[data["Team"].isin(selected_teams)]
    elif selected_weeks:
        filtered_data = data[data["Week Number"].isin(selected_weeks)]
    elif selected_employees:
        filtered_data = data[data["Name"].isin(selected_employees)]
    elif selected_projects:
        filtered_data = data[data["Projects"].apply(lambda x: any(project["name"] in selected_projects for project in x if isinstance(project, dict)))]
    else:
        filtered_data = data
    return filtered_data

filtered_data = filter_data(data, selected_teams, selected_weeks, selected_employees, selected_projects)

# Main content
st.title("CEO Dashboard")

with st.container():
    st.header("Key Metrics")

# Key Metrics
try:
    total_tasks = filtered_data["Number of Completed Tasks"].sum() + filtered_data["Number of Pending Tasks"].sum() + filtered_data["Number of Dropped Tasks"].sum()
    completed_tasks = filtered_data["Number of Completed Tasks"].sum()
    pending_tasks = filtered_data["Number of Pending Tasks"].sum()
    dropped_tasks = filtered_data["Number of Dropped Tasks"].sum()
except KeyError as e:
    st.error(f"The following column is missing in the data: {str(e)}")
    total_tasks = completed_tasks = pending_tasks = dropped_tasks = 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Tasks", total_tasks)
col2.metric("Completed Tasks", completed_tasks)
col3.metric("Pending Tasks", pending_tasks)
col4.metric("Dropped Tasks", dropped_tasks)

st.divider()

# Productivity Trends
with st.container():
    st.header("Productivity Trends")
try:
    productivity_data = filtered_data[["Week Number", "Productivity Rating"]]
    avg_productivity = productivity_data.groupby("Week Number")["Productivity Rating"].mean()
except KeyError as e:
    st.error(f"The following column is missing in the data: {str(e)}")
    avg_productivity = pd.Series(dtype=float)

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(avg_productivity.index, avg_productivity.values, marker="o", color="blue", linewidth=2)
ax.set_xlabel("Week Number", fontsize=12)
ax.set_ylabel("Average Productivity Rating", fontsize=12)
ax.set_title("Productivity Trends", fontsize=16)
ax.grid(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
st.pyplot(fig)

# Team Performance
col1, col2 = st.columns([2, 1])  # Adjust the column widths

with col1:
    st.subheader("Team Performance")
    
try:
    team_data = filtered_data.groupby("Team").agg({
        "Number of Completed Tasks": "sum",
        "Number of Pending Tasks": "sum",
        "Number of Dropped Tasks": "sum",
        "Productivity Rating": "mean"
    }).reset_index()
except KeyError as e:
    st.error(f"The following column is missing in the data: {str(e)}")
    team_data = pd.DataFrame(columns=["Team"])

team_data["Total Tasks"] = team_data["Number of Completed Tasks"] + team_data["Number of Pending Tasks"] + team_data["Number of Dropped Tasks"]
team_data["Completion Rate"] = team_data["Number of Completed Tasks"] / team_data["Total Tasks"]

styled_team_data = team_data.style.set_properties(**{'text-align': 'center'}).set_table_styles([
    {'selector': 'th', 'props': [('background-color', '#f0f0f0'), ('color', '#000000'), ('font-weight', 'bold')]},
    {'selector': 'td', 'props': [('padding', '8px')]}
])
st.write(styled_team_data.to_html(index=False), unsafe_allow_html=True)

#Add a bar chart for team performance
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(team_data["Team"], team_data["Number of Completed Tasks"], color="green", label="Completed Tasks")
ax.bar(team_data["Team"], team_data["Number of Pending Tasks"], bottom=team_data["Number of Completed Tasks"], color="orange", label="Pending Tasks")
ax.bar(team_data["Team"], team_data["Number of Dropped Tasks"], bottom=team_data["Number of Completed Tasks"] + team_data["Number of Pending Tasks"], color="red", label="Dropped Tasks")
ax.set_xlabel("Team", fontsize=12)
ax.set_ylabel("Number of Tasks", fontsize=12)
ax.set_title("Team Performance", fontsize=16)
ax.legend(loc="upper right", fontsize=10)
plt.xticks(rotation=45)

# Add interactivity to the chart
def on_bar_click(event):
    if event.inaxes == ax:
        bar_index = event.ind[0]
        team_name = team_data["Team"].iloc[bar_index]
        st.write(f"Detailed information for {team_name} team:")

        # Display detailed information for the selected team
        with st.container():
            st.subheader("Team Performance Drilldown")
            selected_team = st.selectbox("Select a Team", data["Team"].unique(), index=bar_index)  # Set initial selection based on clicked bar
            team_filtered_data = data[data["Team"] == selected_team]

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(team_filtered_data["Name"], team_filtered_data["Number of Completed Tasks"], color="green", label="Completed Tasks")
            ax.bar(team_filtered_data["Name"], team_filtered_data["Number of Pending Tasks"], bottom=team_filtered_data["Number of Completed Tasks"], color="orange", label="Pending Tasks")
            ax.bar(team_filtered_data["Name"], team_filtered_data["Number of Dropped Tasks"], bottom=team_filtered_data["Number of Completed Tasks"] + team_filtered_data["Number of Pending Tasks"], color="red", label="Dropped Tasks")
            ax.set_xlabel("Employee", fontsize=12)
            ax.set_ylabel("Number of Tasks", fontsize=12)
            ax.set_title(f"Performance Drilldown - {selected_team}", fontsize=16)
            ax.legend(loc="upper right", fontsize=10)
            plt.xticks(rotation=45)
            st.pyplot(fig)


fig.canvas.mpl_connect("pick_event", on_bar_click)

# Enable picking on individual bars
for bar in bars:
    bar.set_picker(5)  # Enable picking with a tolerance of 5 pixels

st.pyplot(fig)

# Top Performers
with col2:
    st.subheader("Top Performers")
top_performers = filtered_data.sort_values("Productivity Rating", ascending=False).head(5)
styled_top_performers = top_performers[["Name", "Team", "Number of Completed Tasks", "Productivity Rating"]].style.set_properties(**{'text-align': 'center'}).set_table_styles([
    {'selector': 'th', 'props': [('background-color', '#f0f0f0'), ('color', '#000000'), ('font-weight', 'bold')]},
    {'selector': 'td', 'props': [('padding', '8px')]}
])
st.write(styled_top_performers.to_html(index=False), unsafe_allow_html=True)

# Peer Evaluation Rankings
with st.container():
    st.header("Peer Evaluation Rankings")

    # Extract peer evaluations and flatten the data
    peer_evaluations = filtered_data["Peer_Evaluations"].dropna().apply(pd.Series)
    
    # Check if peer_evaluations is empty
    if peer_evaluations.empty:
        st.write("No peer evaluations available in the filtered data.")
    else:
        # Normalize the peer evaluations data
        peer_evaluations = pd.json_normalize(peer_evaluations[0])
        peer_evaluations['Rating'] = pd.to_numeric(peer_evaluations['Rating'], errors='coerce')
        
        # Extract only the name part from the "Peer" column BEFORE converting to numeric
        peer_evaluations['Peer'] = peer_evaluations['Peer'].astype(str).apply(lambda x: x.split(' (')[0])

        # Calculate the average peer rating for each employee
        employee_ratings = peer_evaluations.groupby(["Peer"])["Rating"].mean().reset_index()
        
        # Merge employee ratings with employee names
        employee_ratings = employee_ratings.merge(filtered_data[["Name"]], left_on="Peer", right_on="Name", how="left")

        # Check if the required columns are present after the merge
        if "Peer" in employee_ratings.columns and "Rating" in employee_ratings.columns:
            # Sort employees based on their average peer rating
            top_rated_employees = employee_ratings.sort_values("Rating", ascending=False)

            # Display the top-rated employees
            styled_peer_rankings = top_rated_employees[["Name", "Rating"]].head(5).style.set_properties(**{'text-align': 'center'}).set_table_styles([
                {'selector': 'th', 'props': [('background-color', '#f0f0f0'), ('color', '#000000'), ('font-weight', 'bold')]},
                {'selector': 'td', 'props': [('padding', '8px')]}
            ])
            st.write(styled_peer_rankings.to_html(index=False), unsafe_allow_html=True)
        else:
            st.write("Peer evaluation data is missing required columns after merge.")

#Provide insights on team collaboration
with st.container():
    st.subheader("Team Collaboration Insights")

    # Initialize top_rated_employees to an empty DataFrame if not defined yet
    top_rated_employees = top_rated_employees if 'top_rated_employees' in locals() else pd.DataFrame() 

    if not top_rated_employees.empty:
        avg_rating = top_rated_employees["Rating"].mean()
        st.write(f"The average peer rating for the selected period is {avg_rating:.2f}.")
        if avg_rating >= 4.0:
            st.write("The team demonstrates excellent collaboration and support for each other.")
        elif avg_rating >= 3.0:
            st.write("The team shows good collaboration and support, with room for improvement.")
        else:
            st.write("The team may need to focus on improving collaboration and supporting each other.")
    else:
        st.write("No peer evaluation data available for team collaboration insights.")

# Projects
try:
    data["Projects"] = data["Projects"].apply(lambda x: x if isinstance(x, list) else [])
except KeyError:
    st.error("The 'Projects' column is missing in the data.")
    data["Projects"] = pd.Series(dtype=object)

with st.container():
    st.header("Projects")
    st.write("This section provides an overview of the projects worked on by each employee during the selected period.")
project_data = filtered_data[filtered_data["Projects"].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)]

if not project_data.empty:
    #Allow sorting or filtering of projects
    st.sidebar.subheader("Project Filters")
    min_completion = st.sidebar.number_input("Minimum Completion %", min_value=0, max_value=100, value=0, step=1)
    max_completion = st.sidebar.number_input("Maximum Completion %", min_value=0, max_value=100, value=100, step=1)
    sort_by = st.sidebar.selectbox("Sort By", ["Completion %", "Project Name"])
    sort_order = st.sidebar.selectbox("Sort Order", ["Ascending", "Descending"])

    project_data["Completion %"] = project_data["Projects"].apply(lambda x: [p["completion"] for p in x])
    project_data = project_data[(project_data["Completion %"].apply(lambda x: min_completion <= min(x) <= max_completion if x else False))]

    if sort_by == "Completion %":
        project_data = project_data.sort_values(by="Completion %", key=lambda x: x.apply(lambda y: max(y) if y else 0), ascending=sort_order=="Ascending")
    else:
        project_data = project_data.sort_values(by="Name", ascending=sort_order=="Ascending")
    # Extract project details and calculate completion percentage
    projects = pd.json_normalize(project_data["Projects"].explode())
    projects["Completion"] = projects["completion"].astype(float)
    project_completion = projects.groupby("name")["Completion"].mean().reset_index()

    # Display project completion table
    st.subheader("Project Completion")
    styled_project_completion = project_completion.style.set_properties(**{'text-align': 'center'}).set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#f0f0f0'), ('color', '#000000'), ('font-weight', 'bold')]},
        {'selector': 'td', 'props': [('padding', '8px')]}
    ])
    st.write(styled_project_completion.to_html(index=False), unsafe_allow_html=True)

    #Add a pie chart for project completion rates
    if not project_completion.empty:
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(project_completion["Completion"], labels=project_completion["name"], autopct="%1.1f%%")
        ax.set_title("Project Completion Rates", fontsize=16)
        st.pyplot(fig)
    else:
        st.write("No project data available.")    

    # Display project details for each employee
    with st.expander("Project Details"):
        selected_employee = st.selectbox("Select an Employee", data["Name"].unique())
        employee_project_data = project_data[project_data["Name"] == selected_employee]

    if not employee_project_data.empty:
        employee_projects = pd.DataFrame(employee_project_data["Projects"].iloc[0])
        employee_projects["Timeline"] = employee_projects.apply(lambda x: f"{x['start_date']} - {x['end_date']}" if "start_date" in x and "end_date" in x else "N/A", axis=1)
        employee_projects["Status"] = employee_projects.apply(lambda x: "Completed" if x["completion"] == 100 else "In Progress", axis=1)
        employee_projects = employee_projects[["name", "Timeline", "completion", "Status"]]
        employee_projects.columns = ["Project", "Timeline", "Completion %", "Status"]
        styled_employee_projects = employee_projects.style.set_properties(**{'text-align': 'center'}).set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#f0f0f0'), ('color', '#000000'), ('font-weight', 'bold')]},
            {'selector': 'td', 'props': [('padding', '8px')]}
        ])
        st.write(styled_employee_projects.to_html(index=False), unsafe_allow_html=True)
    else:
        st.write("No project data available for the selected employee.")
else:
    st.write("No projects found.")

# Raw Data
with st.container():
    st.header("Raw Data")
display_data()