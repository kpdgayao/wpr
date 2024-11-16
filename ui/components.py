# ui/components.py
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd

class UIComponents:
    @staticmethod
    def load_custom_css():
        """Load custom CSS styles"""
        custom_css = """
            <style>
                .title {
                    font-size: 36px;
                    font-weight: bold;
                    color: #2E86C1;
                    margin-bottom: 20px;
                    text-align: center;
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
                    padding: 10px;
                    border-radius: 5px;
                    background-color: #EAFAF1;
                }
                .warning-message {
                    font-size: 18px;
                    font-weight: bold;
                    color: #F39C12;
                    margin-top: 20px;
                    padding: 10px;
                    border-radius: 5px;
                    background-color: #FEF9E7;
                }
                .stButton>button {
                    background-color: #2E86C1;
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 5px;
                    border: none;
                    transition: all 0.3s ease;
                }
                .stButton>button:hover {
                    background-color: #21618C;
                    transform: translateY(-2px);
                }
            </style>
        """
        st.markdown(custom_css, unsafe_allow_html=True)

    @staticmethod
    def display_header(week_number: int):
        """Display page header with current date and week information"""
        st.markdown('<div class="title">IOL Weekly Productivity Report (WPR)</div>', 
                   unsafe_allow_html=True)
        
        current_date = datetime.now().strftime("%B %d, %Y")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Date Today: {current_date}")
        with col2:
            st.write(f"Week Number: {week_number}")

    @staticmethod
    def display_user_history(user_data: pd.DataFrame):
        """Display user's historical data with visualizations"""
        if not user_data.empty:
            st.markdown('<div class="section-header">Your Recent Activity</div>', 
                       unsafe_allow_html=True)
            
            # Create productivity trend chart
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
            
            # Productivity Rating Trend
            ax1.plot(user_data["Week Number"], 
                    user_data["Productivity Rating"].str[0].astype(int), 
                    marker='o')
            ax1.set_title("Productivity Rating Trend")
            ax1.set_xlabel("Week Number")
            ax1.set_ylabel("Rating")
            ax1.grid(True)
            
            # Task Distribution
            completed = user_data["Number of Completed Tasks"]
            pending = user_data["Number of Pending Tasks"]
            dropped = user_data["Number of Dropped Tasks"]
            
            ax2.bar(user_data["Week Number"], completed, label="Completed", 
                   color='#28B463')
            ax2.bar(user_data["Week Number"], pending, bottom=completed, 
                   label="Pending", color='#F4D03F')
            ax2.bar(user_data["Week Number"], dropped, 
                   bottom=completed+pending, label="Dropped", color='#E74C3C')
            ax2.set_title("Task Distribution Over Time")
            ax2.set_xlabel("Week Number")
            ax2.set_ylabel("Number of Tasks")
            ax2.legend()
            
            plt.tight_layout()
            st.pyplot(fig)

    @staticmethod
    def display_task_section():
        """Display task input section"""
        st.markdown('<div class="section-header">Task Management</div>', 
                   unsafe_allow_html=True)
        
        completed_tasks = st.text_area(
            "Completed Tasks (one per line)",
            help="List all tasks you completed this week"
        )
        
        pending_tasks = st.text_area(
            "Pending Tasks (one per line)",
            help="List all tasks that are still in progress"
        )
        
        dropped_tasks = st.text_area(
            "Dropped Tasks (one per line)",
            help="List all tasks that were dropped or cancelled"
        )
        
        return completed_tasks, pending_tasks, dropped_tasks

    @staticmethod
    def display_project_section():
        """Display project input section"""
        st.markdown('<div class="section-header">Project Progress</div>', 
                   unsafe_allow_html=True)
        
        projects = st.text_area(
            "Projects and Completion Percentage",
            help="Enter each project in format: Project Name, Completion% (e.g., 'Website Redesign, 75')"
        )
        
        return projects

    @staticmethod
    def display_productivity_section(config):
        """Display productivity evaluation section"""
        st.markdown('<div class="section-header">Productivity Evaluation</div>', 
                   unsafe_allow_html=True)
        
        productivity_rating = st.select_slider(
            "Rate your productivity this week",
            options=config.productivity_ratings
        )
        
        productivity_suggestions = st.multiselect(
            "What would help improve your productivity?",
            options=config.productivity_suggestions
        )
        
        productivity_details = st.text_area(
            "Additional Details",
            help="Provide more context about your productivity this week"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            productive_time = st.radio(
                "Most productive time",
                options=config.time_slots
            )
        
        with col2:
            productive_place = st.radio(
                "Preferred work location",
                options=config.work_locations
            )
        
        return (productivity_rating, productivity_suggestions, 
                productivity_details, productive_time, productive_place)

    @staticmethod
    def display_peer_evaluation_section(teammates):
        """Display peer evaluation section"""
        st.markdown('<div class="section-header">Peer Evaluation</div>', 
                   unsafe_allow_html=True)
        
        selected_peers = st.multiselect(
            "Select teammates you worked with this week",
            options=teammates
        )
        
        peer_ratings = {}
        for peer in selected_peers:
            rating = st.radio(
                f"Rate {peer}",
                options=["1 (Poor)", "2 (Fair)", "3 (Good)", "4 (Excellent)"],
                key=f"peer_rating_{peer}"
            )
            peer_ratings[peer] = rating
        
        return peer_ratings