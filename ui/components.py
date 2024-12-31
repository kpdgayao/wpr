# ui/components.py
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import logging 

# Configure logging if not already configured elsewhere
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('wpr.log')
    ]
)

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
    def display_task_section(default_completed='', default_pending='', default_dropped=''):
        """Display task input section with default values"""
        st.markdown('<div class="section-header">Task Management</div>', 
                   unsafe_allow_html=True)
        
        completed_tasks = st.text_area(
            "Completed Tasks (one per line)",
            value=default_completed,
            help="List all tasks you completed this week"
        )
        
        pending_tasks = st.text_area(
            "Pending Tasks (one per line)",
            value=default_pending,
            help="List all tasks that are still in progress"
        )
        
        dropped_tasks = st.text_area(
            "Dropped Tasks (one per line)",
            value=default_dropped,
            help="List all tasks that were dropped or cancelled"
        )
        
        return completed_tasks, pending_tasks, dropped_tasks

    @staticmethod
    def display_project_section(default_projects=''):
        """Display project input section with default values"""
        st.markdown('<div class="section-header">Project Progress</div>', 
                   unsafe_allow_html=True)
        
        projects = st.text_area(
            "Projects and Completion Percentage",
            value=default_projects,
            help="Enter each project in format: Project Name, Completion% (e.g., 'Website Redesign, 75')"
        )
        
        return projects

    @staticmethod
    def display_productivity_section(config, defaults=None, edit_mode=False):
        """Display productivity evaluation section with default values"""
        if defaults is None:  # Initialize empty defaults if None
            defaults = {}
                
        st.markdown('<div class="section-header">Productivity Evaluation</div>', 
                   unsafe_allow_html=True)
        
        # Fix for productivity rating slider
        try:
            current_value = defaults.get('productivity_rating')
            # If we have a valid current value, find its index in the options
            default_index = 0
            if current_value:
                if current_value in config.PRODUCTIVITY_RATINGS:
                    default_index = config.PRODUCTIVITY_RATINGS.index(current_value)
            
            # Display productivity rating selector
            if edit_mode:
                productivity_rating = st.selectbox(
                    "Productivity Rating",
                    options=config.PRODUCTIVITY_RATINGS,
                    value=config.PRODUCTIVITY_RATINGS[default_index]
                )
            else:
                productivity_rating = st.radio(
                    "Productivity Rating",
                    options=config.PRODUCTIVITY_RATINGS
                )
        except (ValueError, IndexError) as e:
            logging.error(f"Error setting productivity slider value: {str(e)}")
            productivity_rating = st.select_slider(
                "Rate your productivity this week",
                options=config.PRODUCTIVITY_RATINGS
            )
        
        productivity_suggestions = st.multiselect(
            "What would help improve your productivity?",
            options=config.productivity_suggestions,
            default=defaults.get('productivity_suggestions', [])
        )
        
        productivity_details = st.text_area(
            "Additional Details",
            value=defaults.get('productivity_details', ''),
            help="Provide more context about your productivity this week"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            # Handle productive time default value
            default_time = defaults.get('productive_time')
            time_index = (
                config.time_slots.index(default_time) 
                if default_time in config.time_slots 
                else 0
            )
            productive_time = st.radio(
                "Most productive time",
                options=config.time_slots,
                index=time_index
            )
        
        with col2:
            # Handle productive place default value
            default_place = defaults.get('productive_place')
            place_index = (
                config.work_locations.index(default_place)
                if default_place in config.work_locations
                else 0
            )
            productive_place = st.radio(
                "Preferred work location",
                options=config.work_locations,
                index=place_index
            )
        
        return (productivity_rating, productivity_suggestions, 
                productivity_details, productive_time, productive_place)

    @staticmethod
    def display_peer_evaluation_section(teammates, default_ratings=None):
        """Display peer evaluation section with default values"""
        if default_ratings is None:
            default_ratings = {}
            
        st.markdown('<div class="section-header">Peer Evaluation</div>', 
                   unsafe_allow_html=True)
        
        selected_peers = st.multiselect(
            "Select teammates you worked with this week",
            options=teammates,
            default=[peer for peer in default_ratings.keys() if peer in teammates]
        )
        
        peer_ratings = {}
        rating_options = ["1 (Poor)", "2 (Fair)", "3 (Good)", "4 (Excellent)"]
        
        for peer in selected_peers:
            default_index = 0
            if peer in default_ratings:
                default_value = default_ratings[peer].get('Rating', 1)
                default_index = default_value - 1 if 1 <= default_value <= 4 else 0
                
            rating = st.radio(
                f"Rate {peer}",
                options=rating_options,
                index=default_index,
                key=f"peer_rating_{peer}"
            )
            peer_ratings[peer] = rating
        
        return peer_ratings