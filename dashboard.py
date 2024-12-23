import streamlit as st
from core.database import DatabaseHandler
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from config.constants import Constants
from utils.data_utils import validate_numeric_columns, calculate_week_stats
from utils.ui_utils import apply_custom_css, display_metric_card, create_filter_section
from config.settings import Config
import logging

# Set page configuration
st.set_page_config(page_title="CEO Dashboard", page_icon=":bar_chart:", layout="wide")

# Apply custom styling
apply_custom_css()

try:
    # Initialize database connection
    config = Config()
    
    # Try to load email config but don't fail if not available
    if not config.load_email_config():
        logging.warning("Email configuration not available. Some features may be limited.")
    
    db = DatabaseHandler(config.SUPABASE_URL, config.SUPABASE_KEY)
except Exception as e:
    st.error("Failed to initialize configuration. Please check your environment variables.")
    st.exception(e)
    st.stop()

# Load data
@st.cache_data(ttl=Constants.CACHE_TTL)
def load_cached_data():
    """Load data with caching enabled and TTL set to 1 hour."""
    data = db.load_data()  # Use the load_data method from DatabaseHandler
    return validate_numeric_columns(data, [
        "Week Number",
        "Number of Completed Tasks",
        "Number of Pending Tasks",
        "Number of Dropped Tasks",
        "Productivity Rating"
    ])

try:
    data = load_cached_data()
    if data.empty:
        st.warning("No data found in the database.")
        st.stop()
except Exception as e:
    st.error("Failed to load data from database. Please check your connection settings.")
    st.exception(e)
    st.stop()

# Create filters
filter_columns = ["Team", "Week Number", "Name"]
filter_labels = {
    "Team": "Select Teams",
    "Week Number": "Select Weeks",
    "Name": "Select Employees"
}
filters = create_filter_section(data, filter_columns, filter_labels)

# Add project filter separately due to its nested structure
selected_projects = st.sidebar.multiselect(
    "Select Projects",
    data["Projects"].apply(lambda x: [project["name"] for project in x if isinstance(project, dict)]).explode().unique()
)

@st.cache_data(ttl=Constants.CACHE_TTL)
def filter_cached_data(data, filters, selected_projects):
    """Filter data based on selected criteria with caching enabled."""
    filtered = data.copy()
    
    for col, selected in filters.items():
        if selected:
            filtered = filtered[filtered[col].isin(selected)]
    
    if selected_projects:
        filtered = filtered[filtered["Projects"].apply(
            lambda x: any(project["name"] in selected_projects 
                        for project in x if isinstance(project, dict))
        )]
    
    return filtered

# Apply filters
filtered_data = filter_cached_data(data, filters, selected_projects)

# Calculate and display metrics
stats = calculate_week_stats(filtered_data)

st.title("CEO Dashboard")

# Display metrics in a grid
col1, col2, col3, col4 = st.columns(4)
with col1:
    display_metric_card("Completed Tasks", int(stats['total_completed']))
with col2:
    display_metric_card("Pending Tasks", int(stats['total_pending']))
with col3:
    display_metric_card("Dropped Tasks", int(stats['total_dropped']))
with col4:
    avg_productivity = stats['avg_productivity']
    display_metric_card("Avg Productivity", f"{avg_productivity:.2f}" if pd.notnull(avg_productivity) else "N/A")

# Productivity Trends
st.header("Productivity Trends")

# Prepare data for line graph
productivity_data = filtered_data.groupby(['Week Number', 'Year']).agg({
    'Productivity Rating': 'mean'
}).reset_index()

# Sort by Year and Week Number
productivity_data = productivity_data.sort_values(['Year', 'Week Number'])

if not productivity_data.empty and pd.notnull(productivity_data['Productivity Rating']).any():
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(range(len(productivity_data)), productivity_data['Productivity Rating'], marker='o')
    ax.set_xticks(range(len(productivity_data)))
    ax.set_xticklabels([f"Week {row['Week Number']}\n{row['Year']}" 
                        for _, row in productivity_data.iterrows()], rotation=45)
    ax.set_xlabel("Time Period")
    ax.set_ylabel("Average Productivity Rating")
    ax.set_title("Productivity Trends Over Time")
    ax.grid(True, linestyle='--', alpha=0.7)
    st.pyplot(fig)
else:
    st.warning("No productivity data available for the selected filters.")

# Team Performance
st.header("Team Performance")

# Calculate team metrics
team_data = filtered_data.groupby("Team").agg({
    "Number of Completed Tasks": "sum",
    "Number of Pending Tasks": "sum",
    "Number of Dropped Tasks": "sum",
    "Productivity Rating": ["mean", "count"]
}).reset_index()

team_data.columns = ["Team", "Number of Completed Tasks", "Number of Pending Tasks", 
                    "Number of Dropped Tasks", "Avg Productivity", "Number of Reports"]

# Format the productivity rating
team_data["Avg Productivity"] = team_data["Avg Productivity"].apply(
    lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A"
)

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
with st.container():
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

    if "Peer_Evaluations" not in filtered_data.columns:
        st.write("The 'Peer_Evaluations' column is missing in the data.")
    else:
        # Extract peer evaluations
        peer_evaluations = filtered_data["Peer_Evaluations"].dropna()

        if peer_evaluations.empty:
            st.write("No peer evaluations available in the filtered data.")
        else:
            # Convert the series to a list
            peer_evaluations_list = peer_evaluations.tolist()
            
            # Extract "Peer" and "Rating" values from the list of dictionaries
            peer_data = []
            for eval_list in peer_evaluations_list:
                for eval_dict in eval_list:
                    if "Peer" in eval_dict and "Rating" in eval_dict:
                        peer_data.append({"Peer": eval_dict["Peer"], "Rating": eval_dict["Rating"]})
            
            if not peer_data:
                st.write("No valid peer evaluations found.")
            else:
                peer_evaluations_df = pd.DataFrame(peer_data)

                # Extract and clean the name part from the "Peer" column
                peer_evaluations_df["Peer"] = peer_evaluations_df["Peer"].astype(str).apply(lambda x: x.split(" (")[0])
                filtered_data["Name"] = filtered_data["Name"].astype(str).apply(lambda x: x.split(" (")[0])

                # Convert ratings to numeric, handling errors
                peer_evaluations_df["Rating"] = pd.to_numeric(peer_evaluations_df["Rating"], errors="coerce")

                # Merge peer evaluations with employee names
                peer_evaluations_df = peer_evaluations_df.merge(filtered_data[["Name"]], left_on="Peer", right_on="Name", how="left")

                # Group by both "Peer" and "Name" columns and calculate the average rating
                employee_ratings = peer_evaluations_df.groupby(["Peer", "Name"])["Rating"].mean().reset_index()

                # Remove NaN ratings or names
                employee_ratings = employee_ratings.dropna(subset=['Rating', 'Name'])

                # Check if there are valid peer evaluations after merging
                if not employee_ratings.empty:
                    # Sort employees based on their average peer rating
                    top_rated_employees = employee_ratings.sort_values("Rating", ascending=False)

                    # Display the top-rated employees
                    styled_peer_rankings = top_rated_employees[["Name", "Rating"]].head(5).style.set_properties(**{'text-align': 'center'}).set_table_styles([
                        {'selector': 'th', 'props': [('background-color', '#f0f0f0'), ('color', '#000000'), ('font-weight', 'bold')]},
                        {'selector': 'td', 'props': [('padding', '8px')]}
                    ])
                    st.write(styled_peer_rankings.to_html(index=False), unsafe_allow_html=True)
                else:
                    st.write("No valid peer evaluations or matching employee names found.")

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

    project_data = filtered_data[filtered_data["Projects"].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)].copy()  

    if not project_data.empty:
        # Allow sorting or filtering of projects
        with st.sidebar: 
            st.subheader("Project Filters")
            min_completion = st.sidebar.number_input("Minimum Completion %", min_value=0, max_value=100, value=0, step=1)
            max_completion = st.sidebar.number_input("Maximum Completion %", min_value=0, max_value=100, value=100, step=1)
            sort_by = st.sidebar.selectbox("Sort By", ["Completion %", "Project Name"])
            sort_order = st.sidebar.selectbox("Sort Order", ["Ascending", "Descending"])

        project_data.loc[:, "Completion %"] = project_data["Projects"].apply(lambda x: [p["completion"] for p in x])  
        project_data = project_data[(project_data["Completion %"].apply(lambda x: min_completion <= min(x) <= max_completion if x else False))]

        if sort_by == "Completion %":
            project_data = project_data.sort_values(by="Completion %", key=lambda x: x.apply(lambda y: max(y) if y else 0), ascending=sort_order=="Ascending")
        else:  # Assuming the project name is stored under the "name" key
            project_data["Project Name"] = project_data["Projects"].apply(lambda x: [p["name"] for p in x])
            project_data = project_data.sort_values(by="Project Name", key=lambda x: x.apply(lambda y: y[0] if y else ''), ascending=sort_order=="Ascending")
            
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

        # Add a pie chart for project completion rates
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
                employee_projects.columns = ["Project Name", "Timeline", "Completion %", "Status"]
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
    
    # Convert list columns to string representation for display
    display_data = filtered_data.copy()
    list_columns = ['Completed Tasks', 'Pending Tasks', 'Dropped Tasks', 
                   'Productivity Suggestions', 'Projects', 'Peer_Evaluations']
    
    for col in list_columns:
        if col in display_data.columns:
            display_data[col] = display_data[col].apply(lambda x: str(x) if x is not None else '[]')
    
    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True
    )