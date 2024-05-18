import streamlit as st
from database import load_data, display_data
import matplotlib.pyplot as plt
import pandas as pd

# Set page configuration
st.set_page_config(page_title="CEO Dashboard", page_icon=":bar_chart:", layout="wide")

# Load data
data = load_data()

# Convert "Productivity Rating" column to numeric
data["Productivity Rating"] = pd.to_numeric(data["Productivity Rating"].str.split(" - ").str[0], errors="coerce")

# Sidebar filters
st.sidebar.header("Filters")
selected_team = st.sidebar.multiselect("Select Team", data["Team"].unique())
selected_week = st.sidebar.multiselect("Select Week Number", data["Week Number"].unique())

# Filter data based on selected team and week
filtered_data = data[(data["Team"].isin(selected_team)) & (data["Week Number"].isin(selected_week))]

# Main content
st.title("CEO Dashboard")

# Key Metrics
total_tasks = filtered_data["Number of Completed Tasks"].sum() + filtered_data["Number of Pending Tasks"].sum() + filtered_data["Number of Dropped Tasks"].sum()
completed_tasks = filtered_data["Number of Completed Tasks"].sum()
pending_tasks = filtered_data["Number of Pending Tasks"].sum()
dropped_tasks = filtered_data["Number of Dropped Tasks"].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Tasks", total_tasks)
col2.metric("Completed Tasks", completed_tasks)
col3.metric("Pending Tasks", pending_tasks)
col4.metric("Dropped Tasks", dropped_tasks)

# Productivity Trends
st.header("Productivity Trends")
productivity_data = filtered_data[["Week Number", "Productivity Rating"]]
avg_productivity = productivity_data.groupby("Week Number")["Productivity Rating"].mean()

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(avg_productivity.index, avg_productivity.values, marker="o")
ax.set_xlabel("Week Number")
ax.set_ylabel("Average Productivity Rating")
ax.grid(True)
st.pyplot(fig)

# Team Performance
st.header("Team Performance")
team_data = filtered_data.groupby("Team").agg({
    "Number of Completed Tasks": "sum",
    "Number of Pending Tasks": "sum",
    "Number of Dropped Tasks": "sum",
    "Productivity Rating": "mean"
}).reset_index()

team_data["Total Tasks"] = team_data["Number of Completed Tasks"] + team_data["Number of Pending Tasks"] + team_data["Number of Dropped Tasks"]
team_data["Completion Rate"] = team_data["Number of Completed Tasks"] / team_data["Total Tasks"]

st.dataframe(team_data)

# Top Performers
st.header("Top Performers")
top_performers = filtered_data.sort_values("Productivity Rating", ascending=False).head(5)
st.table(top_performers[["Name", "Team", "Number of Completed Tasks", "Productivity Rating"]])

# Peer Evaluation Rankings
st.header("Peer Evaluation Rankings")

# Extract peer evaluations and flatten the data
peer_evaluations = pd.json_normalize(filtered_data["Peer_Evaluations"].dropna())

if not peer_evaluations.empty:
    if "Peer" in peer_evaluations.columns and "Rating" in peer_evaluations.columns:
        # Calculate the average peer rating for each employee
        employee_ratings = peer_evaluations.groupby(["Peer"])["Rating"].mean().reset_index()

        # Merge employee ratings with employee names
        employee_ratings = employee_ratings.merge(filtered_data[["Name"]], left_on="Peer", right_on="Name", how="left")

        # Sort employees based on their average peer rating
        top_rated_employees = employee_ratings.sort_values("Rating", ascending=False)

        # Display the top-rated employees
        st.table(top_rated_employees[["Name", "Rating"]].head(5))
    else:
        st.write("Peer evaluation data is missing required columns.")
else:
    st.write("No peer evaluations available.")

# Projects
st.header("Projects")
project_data = filtered_data[filtered_data["Projects"].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)]

if not project_data.empty:
    # Extract project details and calculate completion percentage
    projects = pd.json_normalize(project_data["Projects"].explode())
    projects["Completion"] = projects["completion"].astype(float)
    project_completion = projects.groupby("name")["Completion"].mean().reset_index()

    # Display project completion table
    st.subheader("Project Completion")
    st.table(project_completion)

    # Display project details for each employee
    st.subheader("Project Details")
    for idx, row in project_data.iterrows():
        st.subheader(row["Name"])
        employee_projects = pd.DataFrame(row["Projects"])
        st.table(employee_projects)
        st.write("---")
else:
    st.write("No projects found.")

# Raw Data
st.header("Raw Data")
display_data()