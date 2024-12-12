# ui/hr_visualizations.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional
import pandas as pd
import logging
from datetime import datetime

class HRVisualizations:
    """Class for handling HR data visualizations"""
    
    @staticmethod
    def display_hr_dashboard(hr_analysis: Dict[str, Any], historical_data: Optional[List[Dict[str, Any]]] = None):
        """Display HR analysis dashboard"""
        try:
            if not hr_analysis:
                st.warning("No HR analysis data available to display.")
                return

            st.markdown("## HR Analytics Dashboard")

            # Performance Metrics
            st.markdown("### 📊 Performance Metrics")
            if hr_analysis.get('performance_metrics'):
                HRVisualizations._display_performance_metrics(hr_analysis.get('performance_metrics', {}))
            else:
                st.info("No performance metrics available.")

            # Skills Assessment
            st.markdown("### 🎯 Skills Assessment")
            if hr_analysis.get('skill_assessment'):
                HRVisualizations._display_skills_assessment(hr_analysis.get('skill_assessment', {}))
            else:
                st.info("No skills assessment data available.")

            # Wellness Indicators
            st.markdown("### 🌟 Wellness Indicators")
            HRVisualizations._display_wellness_indicators(hr_analysis.get('wellness_indicators', {}))

            # Risk Assessment
            st.markdown("### ⚠️ Risk Assessment")
            HRVisualizations._display_risk_assessment(hr_analysis.get('risk_factors', {}))

            # Growth Recommendations
            st.markdown("### 📈 Growth Recommendations")
            HRVisualizations._display_recommendations(hr_analysis.get('growth_recommendations', {}))

            # Historical Trends
            if historical_data:
                st.markdown("### 📊 Historical Trends")
                HRVisualizations._display_historical_trends(historical_data)

        except Exception as e:
            logging.error(f"Error displaying HR dashboard: {str(e)}")
            st.error("Error displaying HR analytics dashboard. Please try again later.")
    
    @staticmethod
    def _display_performance_metrics(metrics: Dict[str, float]):
        """Display performance metrics section"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                HRVisualizations._metric_gauge(
                    "Productivity Score",
                    metrics.get('productivity_score', 0),
                    max_value=4,
                    unique_id=f"prod_{timestamp}"
                )
            
            with col2:
                HRVisualizations._metric_gauge(
                    "Task Completion",
                    metrics.get('task_completion_rate', 0),
                    max_value=100,
                    suffix="%",
                    unique_id=f"task_{timestamp}"
                )
            
            with col3:
                HRVisualizations._metric_gauge(
                    "Project Progress",
                    metrics.get('project_progress', 0),
                    max_value=100,
                    suffix="%",
                    unique_id=f"proj_{timestamp}"
                )
            
            with col4:
                HRVisualizations._metric_gauge(
                    "Collaboration",
                    metrics.get('collaboration_score', 0),
                    max_value=4,
                    unique_id=f"collab_{timestamp}"
                )
        except Exception as e:
            logging.error(f"Error displaying performance metrics: {str(e)}")
            st.error("Error displaying performance metrics.")

    @staticmethod
    def _metric_gauge(title: str, value: float, max_value: float, suffix: str = "", unique_id: str = ""):
        """Create a gauge chart for metrics"""
        try:
            unique_key = f"gauge_{title}_{unique_id}".lower().replace(" ", "_")
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=value,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': title},
                number={'suffix': suffix},
                gauge={
                    'axis': {'range': [0, max_value]},
                    'bar': {'color': "#2E86C1"},
                    'steps': [
                        {'range': [0, max_value/3], 'color': "#F8F9F9"},
                        {'range': [max_value/3, 2*max_value/3], 'color': "#EBF5FB"},
                        {'range': [2*max_value/3, max_value], 'color': "#D4E6F1"}
                    ]
                }
            ))
            
            fig.update_layout(height=200)
            st.plotly_chart(fig, use_container_width=True, key=unique_key)
        except Exception as e:
            logging.error(f"Error creating metric gauge: {str(e)}")
            st.error(f"Error displaying {title} metric.")

    @staticmethod
    def _display_skills_assessment(skills: Dict[str, List[str]]):
        """Display skills assessment section"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            col1, col2 = st.columns(2)
            
            with col1:
                HRVisualizations._skills_radar_chart(skills, f"radar_{timestamp}")
            
            with col2:
                HRVisualizations._development_areas_chart(skills, f"dev_{timestamp}")
        except Exception as e:
            logging.error(f"Error displaying skills assessment: {str(e)}")
            st.error("Error displaying skills assessment.")

    @staticmethod
    def _skills_radar_chart(skills: Dict[str, List[str]], unique_id: str):
        """Create radar chart for skills"""
        try:
            categories = ['Technical', 'Soft Skills', 'Leadership', 'Communication']
            values = [
                len(skills.get('technical_skills', [])),
                len(skills.get('soft_skills', [])),
                sum(1 for skill in skills.get('strengths', []) if 'lead' in skill.lower()),
                sum(1 for skill in skills.get('soft_skills', []) if 'communicat' in skill.lower())
            ]

            fig = go.Figure(data=go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Skills'
            ))

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, max(values)+1])),
                showlegend=False,
                title="Skills Distribution"
            )
            
            st.plotly_chart(fig, use_container_width=True, key=f"skills_radar_{unique_id}")
        except Exception as e:
            logging.error(f"Error creating skills radar chart: {str(e)}")
            st.error("Error displaying skills radar chart.")

    @staticmethod
    def _development_areas_chart(skills: Dict[str, List[str]], unique_id: str):
        """Create bar chart for development areas"""
        try:
            development_areas = skills.get('development_areas', [])
            if not development_areas:
                st.info("No development areas identified.")
                return
                
            fig = go.Figure(data=[
                go.Bar(
                    x=[area for area in development_areas],
                    y=[1 for _ in development_areas],
                    text=development_areas,
                    textposition='auto',
                )
            ])
            
            fig.update_layout(
                title="Areas for Development",
                showlegend=False,
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True, key=f"dev_areas_{unique_id}")
        except Exception as e:
            logging.error(f"Error creating development areas chart: {str(e)}")
            st.error("Error displaying development areas.")

    @staticmethod
    def _display_recommendations(recommendations: Dict[str, List[str]]):
        """Display growth recommendations in a formatted manner"""
        try:
            # Ensure we have a recommendations dictionary
            if not recommendations or not isinstance(recommendations, dict):
                st.info("No recommendations available.")
                return
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

            # Display immediate actions with icons and formatting
            immediate_actions = recommendations.get('immediate_actions', [])
            if immediate_actions:
                for i, action in enumerate(immediate_actions):
                    st.info(f"📌 {action}", key=f"action_{i}_{timestamp}")
            else:
                st.info("No immediate actions recommended.")
            
            # Display development goals in an expander
            with st.expander("Long-term Development Goals"):
                development_goals = recommendations.get('development_goals', [])
                if development_goals:
                    for i, goal in enumerate(development_goals):
                        st.write(f"🎯 {goal}", key=f"goal_{i}_{timestamp}")
                else:
                    st.write("No long-term goals set yet.")
            
            # Display training needs if available
            training_needs = recommendations.get('training_needs', [])
            if training_needs:
                with st.expander("Recommended Training"):
                    for i, training in enumerate(training_needs):
                        st.write(f"📚 {training}", key=f"training_{i}_{timestamp}")
                    
        except Exception as e:
            logging.error(f"Error displaying recommendations: {str(e)}")
            st.error("Error displaying recommendations.")