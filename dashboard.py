import streamlit as st
from database import load_data, display_data
import matplotlib.pyplot as plt

# Set page configuration
st.set_page_config(page_title="CEO Dashboard", page_icon=":bar_chart:", layout="wide")

# Load data
data = load_data()

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

# Raw Data
st.header("Raw Data")
display_data()