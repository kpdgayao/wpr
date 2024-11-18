# ui/hr_visualizations.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional
import pandas as pd
import logging

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
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                HRVisualizations._metric_gauge(
                    "Productivity Score",
                    metrics.get('productivity_score', 0),
                    max_value=4,
                    key_suffix="prod"
                )
            
            with col2:
                HRVisualizations._metric_gauge(
                    "Task Completion",
                    metrics.get('task_completion_rate', 0),
                    max_value=100,
                    suffix="%",
                    key_suffix="task"
                )
            
            with col3:
                HRVisualizations._metric_gauge(
                    "Project Progress",
                    metrics.get('project_progress', 0),
                    max_value=100,
                    suffix="%",
                    key_suffix="proj"
                )
            
            with col4:
                HRVisualizations._metric_gauge(
                    "Collaboration",
                    metrics.get('collaboration_score', 0),
                    max_value=4,
                    key_suffix="collab"
                )
        except Exception as e:
            logging.error(f"Error displaying performance metrics: {str(e)}")
            st.error("Error displaying performance metrics.")

    @staticmethod
    def _metric_gauge(title: str, value: float, max_value: float, suffix: str = "", key_suffix: str = ""):
        """Create a gauge chart for metrics with unique key"""
        try:
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
            # Add unique key for each chart
            st.plotly_chart(fig, use_container_width=True, key=f"gauge_{title}_{key_suffix}".lower().replace(" ", "_"))
        except Exception as e:
            logging.error(f"Error creating metric gauge: {str(e)}")
            st.error(f"Error displaying {title} metric.")

    @staticmethod
    def _display_skills_assessment(skills: Dict[str, List[str]]):
        """Display skills assessment section"""
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                HRVisualizations._skills_radar_chart(skills)
            
            with col2:
                HRVisualizations._development_areas_chart(skills)
        except Exception as e:
            logging.error(f"Error displaying skills assessment: {str(e)}")
            st.error("Error displaying skills assessment.")

    @staticmethod
    def _skills_radar_chart(skills: Dict[str, List[str]]):
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
            
            # Add unique key for radar chart
            st.plotly_chart(fig, use_container_width=True, key="skills_radar_chart")
        except Exception as e:
            logging.error(f"Error creating skills radar chart: {str(e)}")
            st.error("Error displaying skills radar chart.")

    @staticmethod
    def _display_wellness_indicators(wellness: Dict[str, str]):
        """Display wellness indicators"""
        try:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Work-Life Balance", 
                        wellness.get('work_life_balance', 'N/A'),
                        key="wellness_balance")
            with col2:
                st.metric("Workload", 
                        wellness.get('workload_assessment', 'N/A'),
                        key="wellness_workload")
            with col3:
                st.metric("Engagement", 
                        wellness.get('engagement_level', 'N/A'),
                        key="wellness_engagement")
        except Exception as e:
            logging.error(f"Error displaying wellness indicators: {str(e)}")
            st.error("Error displaying wellness indicators.")

    @staticmethod
    def _display_historical_trends(historical_data: List[Dict[str, Any]]):
        try:
            if not historical_data:
                st.info("No historical data available.")
                return

            df = pd.DataFrame(historical_data)
            
            # Performance trend
            fig = px.line(df, 
                        x='week_number', 
                        y=['productivity_score', 'collaboration_score'],
                        title='Performance Trends Over Time',
                        labels={
                            'week_number': 'Week Number',
                            'productivity_score': 'Productivity Score',
                            'collaboration_score': 'Collaboration Score'
                        })
            
            fig.update_layout(
                xaxis_title="Week Number",
                yaxis_title="Score",
                legend_title="Metrics",
                hovermode='x unified'
            )
            
            # Add unique key for trends chart
            st.plotly_chart(fig, use_container_width=True, key="historical_trends_chart")
        except Exception as e:
            logging.error(f"Error displaying historical trends: {str(e)}")
            st.error("Error displaying historical trends.")

    @staticmethod
    def _display_recommendations(recommendations: Dict[str, List[str]]):
        try:
            immediate_actions = recommendations.get('immediate_actions', [])
            if immediate_actions:
                for i, action in enumerate(immediate_actions):
                    st.info(f"📌 {action}", key=f"action_{i}")  # Add key
            else:
                st.info("No immediate actions recommended.", key="no_actions")
            
            with st.expander("View Long-term Development Goals"):
                development_goals = recommendations.get('development_goals', [])
                if development_goals:
                    for i, goal in enumerate(development_goals):
                        st.write(f"🎯 {goal}", key=f"goal_{i}")  # Add key
                else:
                    st.write("No long-term goals set.", key="no_goals")
        except Exception as e:
            logging.error(f"Error displaying recommendations: {str(e)}")
            st.error("Error displaying recommendations.")
    
    @staticmethod
    def _development_areas_chart(skills: Dict[str, List[str]]):
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
            
            st.plotly_chart(fig, use_container_width=True, key="dev_areas_chart")
        except Exception as e:
            logging.error(f"Error creating development areas chart: {str(e)}")
            st.error("Error displaying development areas.")

    @staticmethod
    def _display_risk_assessment(risk_factors: Dict[str, str]):
        try:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Burnout Risk", 
                    risk_factors.get('burnout_risk', 'N/A'),
                    delta=None,
                    help="Assessment of potential burnout based on workload and engagement",
                    key="risk_burnout"  # Add key
                )
                
            with col2:
                st.metric(
                    "Retention Risk",
                    risk_factors.get('retention_risk', 'N/A'),
                    delta=None,
                    help="Assessment of retention likelihood",
                    key="risk_retention"  # Add key
                )
                
            with col3:
                st.metric(
                    "Performance Trend",
                    risk_factors.get('performance_trend', 'N/A'),
                    delta=None,
                    help="Overall performance trajectory",
                    key="risk_performance"  # Add key
                )
                
        except Exception as e:
            logging.error(f"Error displaying risk assessment: {str(e)}")
            st.error("Error displaying risk metrics.")