# ui/hr_visualizations.py
import streamlit as st
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

class HRVisualizations:
    """Simplified HR dashboard visualization"""
    
    @staticmethod
    def display_hr_dashboard(hr_analysis: Dict[str, Any], historical_data: Optional[List[Dict[str, Any]]] = None):
        """Display simplified HR analysis dashboard"""
        try:
            if not hr_analysis:
                st.warning("No HR analysis data available to display.")
                return

            st.markdown("## HR Analysis Dashboard")

            # Performance Overview
            st.markdown("### 📊 Performance Overview")
            HRVisualizations._display_performance_overview(hr_analysis.get('performance_metrics', {}))

            # Skills & Development
            st.markdown("### 🎯 Skills & Development")
            HRVisualizations._display_skills_overview(hr_analysis.get('skill_assessment', {}))

            # Recommendations
            st.markdown("### 💡 Growth & Recommendations")
            HRVisualizations._display_recommendations(hr_analysis.get('growth_recommendations', {}))

            # Wellness & Risk Factors
            st.markdown("### 🌟 Wellness Overview")
            col1, col2 = st.columns(2)
            with col1:
                HRVisualizations._display_wellness(hr_analysis.get('wellness_indicators', {}))
            with col2:
                HRVisualizations._display_risk_factors(hr_analysis.get('risk_factors', {}))

        except Exception as e:
            logging.error(f"Error displaying HR dashboard: {str(e)}")
            st.error("Error displaying HR analytics dashboard. Please try again later.")

    @staticmethod
    def _display_performance_overview(metrics: Dict[str, float]):
        """Display simplified performance metrics"""
        try:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Productivity",
                    f"{metrics.get('productivity_score', 0)}/4",
                    help="Overall productivity rating"
                )
            
            with col2:
                st.metric(
                    "Task Completion",
                    f"{metrics.get('task_completion_rate', 0)}%",
                    help="Percentage of completed tasks"
                )
            
            with col3:
                st.metric(
                    "Project Progress",
                    f"{metrics.get('project_progress', 0)}%",
                    help="Overall project completion rate"
                )
            
            with col4:
                st.metric(
                    "Collaboration",
                    f"{metrics.get('collaboration_score', 0)}/4",
                    help="Team collaboration rating"
                )
                
        except Exception as e:
            logging.error(f"Error displaying performance overview: {str(e)}")
            st.error("Error displaying performance metrics.")

    @staticmethod
    def _display_skills_overview(skills: Dict[str, List[str]]):
        """Display simplified skills assessment"""
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 💪 Strengths")
                strengths = skills.get('strengths', [])
                if strengths:
                    for strength in strengths:
                        st.success(f"✓ {strength}")
                else:
                    st.info("No strengths identified yet.")
            
            with col2:
                st.markdown("#### 📈 Development Areas")
                dev_areas = skills.get('development_areas', [])
                if dev_areas:
                    for area in dev_areas:
                        st.warning(f"→ {area}")
                else:
                    st.info("No development areas identified.")
                    
        except Exception as e:
            logging.error(f"Error displaying skills overview: {str(e)}")
            st.error("Error displaying skills assessment.")

    @staticmethod
    def _display_recommendations(recommendations: Dict[str, List[str]]):
        """Display simplified recommendations"""
        try:
            # Immediate Actions
            st.markdown("#### 🎯 Priority Actions")
            immediate_actions = recommendations.get('immediate_actions', [])
            if immediate_actions:
                for action in immediate_actions:
                    st.info(f"📌 {action}")
            else:
                st.info("No immediate actions recommended.")

            # Development Goals
            with st.expander("View Development Goals"):
                goals = recommendations.get('development_goals', [])
                if goals:
                    for goal in goals:
                        st.write(f"🎯 {goal}")
                else:
                    st.write("No development goals set yet.")

            # Training Recommendations
            with st.expander("View Training Recommendations"):
                training = recommendations.get('training_needs', [])
                if training:
                    for item in training:
                        st.write(f"📚 {item}")
                else:
                    st.write("No specific training recommended at this time.")
                    
        except Exception as e:
            logging.error(f"Error displaying recommendations: {str(e)}")
            st.error("Error displaying recommendations.")

    @staticmethod
    def _display_wellness(wellness: Dict[str, str]):
        """Display wellness indicators"""
        try:
            st.markdown("#### Wellness Indicators")
            
            # Work-Life Balance
            balance = wellness.get('work_life_balance', 'N/A')
            st.write(f"🔋 Work-Life Balance: {balance}")
            
            # Workload
            workload = wellness.get('workload_assessment', 'N/A')
            st.write(f"📊 Workload: {workload}")
            
            # Engagement
            engagement = wellness.get('engagement_level', 'N/A')
            st.write(f"⭐ Engagement: {engagement}")
            
        except Exception as e:
            logging.error(f"Error displaying wellness indicators: {str(e)}")
            st.error("Error displaying wellness information.")

    @staticmethod
    def _display_risk_factors(risk_factors: Dict[str, str]):
        """Display risk assessment"""
        try:
            st.markdown("#### Risk Assessment")
            
            # Risk Indicators
            burnout = risk_factors.get('burnout_risk', 'N/A')
            retention = risk_factors.get('retention_risk', 'N/A')
            trend = risk_factors.get('performance_trend', 'N/A')
            
            st.write(f"🔥 Burnout Risk: {burnout}")
            st.write(f"🎯 Retention Risk: {retention}")
            st.write(f"📈 Performance Trend: {trend}")
            
        except Exception as e:
            logging.error(f"Error displaying risk factors: {str(e)}")
            st.error("Error displaying risk assessment.")