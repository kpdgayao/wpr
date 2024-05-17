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

# Most Highly Rated Employee
st.header("Most Highly Rated Employee")
peer_ratings = {}
for _, row in filtered_data.iterrows():
    employee = row["Name"]
    ratings = row.get("Peer Ratings", [])  # Use get() method to handle missing "Peer Ratings" column
    if ratings:
        avg_rating = sum(ratings) / len(ratings)
        peer_ratings[employee] = avg_rating

if peer_ratings:
    top_employee = max(peer_ratings, key=peer_ratings.get)
    top_rating = peer_ratings[top_employee]
    st.write(f"Employee: {top_employee}")
    st.write(f"Average Peer Rating: {top_rating:.2f}")
else:
    st.write("No peer ratings available.")

# Past Responses
st.header("Past Responses")
selected_name = st.selectbox("Select User", data["Name"].unique())
past_responses = data[data["Name"] == selected_name].sort_values("Week Number", ascending=False).head(5)
for idx, response in past_responses.iterrows():
    st.subheader(f"Week {response['Week Number']}")
    st.write(f"Productivity Rating: {response['Productivity Rating']}")
    st.write(f"Completed Tasks: {response['Number of Completed Tasks']}")
    st.write(f"Pending Tasks: {response['Number of Pending Tasks']}")
    st.write(f"Dropped Tasks: {response['Number of Dropped Tasks']}")
    st.write("---")

# Projects
st.header("Projects")
project_data = filtered_data[filtered_data["Projects"].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)]
if not project_data.empty:
    for idx, row in project_data.iterrows():
        st.subheader(row["Name"])
        projects = row["Projects"]
        if isinstance(projects, list):
            for project in projects:
                st.write(f"{project['name']}: {project['completion']}%")
        else:
            st.write("No project details available")
        st.write("---")
else:
    st.write("No projects found.")

# Raw Data
st.header("Raw Data")
display_data()