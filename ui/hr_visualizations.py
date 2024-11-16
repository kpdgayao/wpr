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
            st.markdown("## HR Analytics Dashboard")

            # Performance Metrics
            st.markdown("### 📊 Performance Metrics")
            HRVisualizations._display_performance_metrics(hr_analysis.get('performance_metrics', {}))

            # Skills Assessment
            st.markdown("### 🎯 Skills Assessment")
            HRVisualizations._display_skills_assessment(hr_analysis.get('skill_assessment', {}))

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
                    max_value=4
                )
            
            with col2:
                HRVisualizations._metric_gauge(
                    "Task Completion",
                    metrics.get('task_completion_rate', 0),
                    max_value=100,
                    suffix="%"
                )
            
            with col3:
                HRVisualizations._metric_gauge(
                    "Project Progress",
                    metrics.get('project_progress', 0),
                    max_value=100,
                    suffix="%"
                )
            
            with col4:
                HRVisualizations._metric_gauge(
                    "Collaboration",
                    metrics.get('collaboration_score', 0),
                    max_value=4
                )
        except Exception as e:
            logging.error(f"Error displaying performance metrics: {str(e)}")
            st.error("Error displaying performance metrics.")

    @staticmethod
    def _metric_gauge(title: str, value: float, max_value: float, suffix: str = ""):
        """Create a gauge chart for metrics"""
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
            st.plotly_chart(fig, use_container_width=True)
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
            
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logging.error(f"Error creating skills radar chart: {str(e)}")
            st.error("Error displaying skills radar chart.")

    @staticmethod
    def _display_wellness_indicators(wellness: Dict[str, str]):
        """Display wellness indicators"""
        try:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Work-Life Balance", wellness.get('work_life_balance', 'N/A'))
            with col2:
                st.metric("Workload", wellness.get('workload_assessment', 'N/A'))
            with col3:
                st.metric("Engagement", wellness.get('engagement_level', 'N/A'))
        except Exception as e:
            logging.error(f"Error displaying wellness indicators: {str(e)}")
            st.error("Error displaying wellness indicators.")

    @staticmethod
    def _display_historical_trends(historical_data: List[Dict[str, Any]]):
        """Display historical trends"""
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
            
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logging.error(f"Error displaying historical trends: {str(e)}")
            st.error("Error displaying historical trends.")

    @staticmethod
    def _display_recommendations(recommendations: Dict[str, List[str]]):
        """Display growth recommendations"""
        try:
            immediate_actions = recommendations.get('immediate_actions', [])
            if immediate_actions:
                for action in immediate_actions:
                    st.info(f"📌 {action}")
            else:
                st.info("No immediate actions recommended.")
            
            with st.expander("View Long-term Development Goals"):
                development_goals = recommendations.get('development_goals', [])
                if development_goals:
                    for goal in development_goals:
                        st.write(f"🎯 {goal}")
                else:
                    st.write("No long-term goals set.")
        except Exception as e:
            logging.error(f"Error displaying recommendations: {str(e)}")
            st.error("Error displaying recommendations.")