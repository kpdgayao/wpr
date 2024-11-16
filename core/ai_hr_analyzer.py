# core/ai_hr_analyzer.py
import logging
from typing import Dict, Any
import anthropic
from datetime import datetime

# At the top of the file, after imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('hr_analysis.log')
    ]
)

class AIHRAnalyzer:
    def __init__(self, anthropic_api_key: str):
        self.client = anthropic.Client(api_key=anthropic_api_key)

    def generate_hr_analysis(self, wpr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate HR analysis using Claude AI"""
        try:
            # Validate input data
            required_fields = ['Name', 'Team', 'Week Number', 'Year']
            for field in required_fields:
                if field not in wpr_data:
                    raise ValueError(f"Missing required field: {field}")

            # Log analysis start
            logging.info(f"Starting HR analysis for {wpr_data['Name']} - Week {wpr_data['Week Number']}")
            
            # Prepare the prompt for HR analysis
            hr_analysis_prompt = self._prepare_hr_analysis_prompt(wpr_data)
            
            # Use retry mechanism for AI request
            response = self._retry_ai_request(hr_analysis_prompt)
            
            # Parse and structure the AI response
            analysis_result = self._parse_ai_response(response.content[0].text)
            
            # Validate analysis result
            self._validate_analysis_result(analysis_result)
            
            # Add metadata
            analysis_result.update({
                'analysis_timestamp': datetime.now().isoformat(),
                'employee_name': wpr_data['Name'],
                'week_number': wpr_data['Week Number'],
                'year': wpr_data['Year'],
                'team': wpr_data['Team']
            })

            logging.info(f"HR analysis completed successfully for {wpr_data['Name']}")
            return analysis_result

        except Exception as e:
            logging.error(f"Error generating HR analysis: {str(e)}")
            raise

    def _validate_analysis_result(self, analysis_result: Dict[str, Any]) -> None:
        """Validate the analysis result structure and data types"""
        try:
            # Validate performance metrics
            perf_metrics = analysis_result.get('performance_metrics', {})
            for metric in ['productivity_score', 'task_completion_rate', 'project_progress', 'collaboration_score']:
                if metric not in perf_metrics:
                    raise ValueError(f"Missing performance metric: {metric}")
                if not isinstance(perf_metrics[metric], (int, float)):
                    raise ValueError(f"Invalid type for {metric}")
                
            # Validate ranges
            if not 1 <= perf_metrics['productivity_score'] <= 4:
                raise ValueError("Productivity score out of range (1-4)")
            if not 0 <= perf_metrics['task_completion_rate'] <= 100:
                raise ValueError("Task completion rate out of range (0-100)")
            if not 0 <= perf_metrics['project_progress'] <= 100:
                raise ValueError("Project progress out of range (0-100)")
            if not 1 <= perf_metrics['collaboration_score'] <= 4:
                raise ValueError("Collaboration score out of range (1-4)")

            # Validate skill assessment
            skill_assessment = analysis_result.get('skill_assessment', {})
            for skill_list in ['technical_skills', 'soft_skills', 'development_areas', 'strengths']:
                if not isinstance(skill_assessment.get(skill_list), list):
                    raise ValueError(f"Invalid {skill_list} format")
                if not all(isinstance(skill, str) for skill in skill_assessment[skill_list]):
                    raise ValueError(f"Invalid skill type in {skill_list}")

            # Validate wellness indicators
            wellness = analysis_result.get('wellness_indicators', {})
            valid_balance_values = ['Good', 'Moderate', 'Needs Attention']
            valid_workload_values = ['Optimal', 'Heavy', 'Light']
            valid_engagement_values = ['High', 'Moderate', 'Low']
            
            if wellness.get('work_life_balance') not in valid_balance_values:
                raise ValueError("Invalid work-life balance value")
            if wellness.get('workload_assessment') not in valid_workload_values:
                raise ValueError("Invalid workload assessment value")
            if wellness.get('engagement_level') not in valid_engagement_values:
                raise ValueError("Invalid engagement level value")

            # Validate growth recommendations
            growth = analysis_result.get('growth_recommendations', {})
            for key in ['immediate_actions', 'development_goals', 'training_needs']:
                if not isinstance(growth.get(key), list):
                    raise ValueError(f"Invalid {key} format")
                if not all(isinstance(item, str) for item in growth[key]):
                    raise ValueError(f"Invalid type in {key}")

            # Validate team dynamics
            team = analysis_result.get('team_dynamics', {})
            for key in ['collaboration_pattern', 'peer_feedback_summary', 'team_impact']:
                if not isinstance(team.get(key), str):
                    raise ValueError(f"Invalid {key} format")

            # Validate risk factors
            risk_factors = analysis_result.get('risk_factors', {})
            valid_risk_levels = ['Low', 'Moderate', 'High']
            valid_trend_values = ['Improving', 'Stable', 'Declining']
            
            if risk_factors.get('burnout_risk') not in valid_risk_levels:
                raise ValueError("Invalid burnout risk level")
            if risk_factors.get('retention_risk') not in valid_risk_levels:
                raise ValueError("Invalid retention risk level")
            if risk_factors.get('performance_trend') not in valid_trend_values:
                raise ValueError("Invalid performance trend value")

        except Exception as e:
            logging.error(f"Analysis result validation failed: {str(e)}")
            raise ValueError(f"Invalid analysis result structure: {str(e)}")

    def _get_hr_system_prompt(self) -> str:
        """Define the system prompt for HR analysis"""
        return """You are an expert HR Analytics AI for IOL Inc., specializing in employee development and performance analysis. 
        Analyze the Weekly Productivity Report (WPR) data and provide structured insights in the following JSON format:

        {
            "performance_metrics": {
                "productivity_score": float (1-4),
                "task_completion_rate": float (0-100),
                "project_progress": float (0-100),
                "collaboration_score": float (1-4)
            },
            "skill_assessment": {
                "technical_skills": [list of identified skills],
                "soft_skills": [list of identified skills],
                "development_areas": [list of areas needing improvement],
                "strengths": [list of strong areas]
            },
            "wellness_indicators": {
                "work_life_balance": string (Good/Moderate/Needs Attention),
                "workload_assessment": string (Optimal/Heavy/Light),
                "engagement_level": string (High/Moderate/Low)
            },
            "growth_recommendations": {
                "immediate_actions": [list of short-term recommendations],
                "development_goals": [list of long-term goals],
                "training_needs": [list of suggested training]
            },
            "team_dynamics": {
                "collaboration_pattern": string,
                "peer_feedback_summary": string,
                "team_impact": string
            },
            "risk_factors": {
                "burnout_risk": string (Low/Moderate/High),
                "retention_risk": string (Low/Moderate/High),
                "performance_trend": string (Improving/Stable/Declining)
            }
        }

        Analyze the data thoroughly and provide specific, actionable insights.
        Focus on patterns, trends, and areas for both improvement and recognition.
        Consider both individual performance and team dynamics.
        """

    def _prepare_hr_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Prepare the prompt for HR analysis"""
        # Format completed tasks for better readability
        completed_tasks = '\n        '.join([
            f"- {task}" for task in data.get('Completed Tasks', [])
        ])

        # Format projects for better readability
        projects = '\n        '.join([
            f"- {project['name']}: {project['completion']}% complete" 
            for project in data.get('Projects', [])
        ])

        # Format peer evaluations
        peer_evals = '\n        '.join([
            f"- {eval['Peer']}: Rating {eval['Rating']}/4" 
            for eval in data.get('Peer_Evaluations', [])
        ])

        return f"""Please analyze this Weekly Productivity Report data:

            Employee Information:
            - Name: {data['Name']}
            - Team: {data['Team']}
            - Week: {data['Week Number']}
            - Year: {data['Year']}

            Task Statistics:
            - Completed Tasks: {len(data.get('Completed Tasks', []))}
            - Pending Tasks: {len(data.get('Pending Tasks', []))}
            - Dropped Tasks: {len(data.get('Dropped Tasks', []))}

            Completed Tasks Details:
            {completed_tasks}

            Project Progress:
            {projects}

            Productivity Metrics:
            - Self-Rating: {data.get('Productivity Rating')}
            - Most Productive Time: {data.get('Productive Time')}
            - Preferred Work Location: {data.get('Productive Place')}
            - Improvement Suggestions: {', '.join(data.get('Productivity Suggestions', []))}
            - Additional Details: {data.get('Productivity Details')}

            Peer Evaluations:
            {peer_evals}

            Please provide a comprehensive HR analysis following the specified JSON structure.
            Focus on actionable insights and specific recommendations.
            """

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate AI response"""
        try:
            # Extract JSON from response (assuming response is properly formatted)
            import json
            # Clean up the response if needed
            clean_response = response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response.replace('```json', '').replace('```', '')
            
            analysis_data = json.loads(clean_response)
            
            # Validate required fields
            required_sections = [
                'performance_metrics', 'skill_assessment', 
                'wellness_indicators', 'growth_recommendations',
                'team_dynamics', 'risk_factors'
            ]
            
            for section in required_sections:
                if section not in analysis_data:
                    raise ValueError(f"Missing required section: {section}")
            
            return analysis_data

        except Exception as e:
            logging.error(f"Error parsing AI response: {str(e)}")
            raise

    def _retry_ai_request(self, prompt: str, max_retries: int = 3) -> anthropic.types.Message:
        """Retry AI request with exponential backoff"""
        from time import sleep
        
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4000,
                    system=self._get_hr_system_prompt(),
                    messages=[{"role": "user", "content": prompt}]
                )
                logging.info("AI request successful")
                return response
            except anthropic.APIError as e:
                if attempt == max_retries - 1:
                    logging.error(f"All retry attempts failed: {str(e)}")
                    raise
                sleep(2 ** attempt)  # Exponential backoff
                logging.warning(f"Retry attempt {attempt + 1} after error: {str(e)}")

    def _safe_format(self, value: Any, default: str = "None") -> str:
        """Safely format values for the prompt"""
        if value is None:
            return default
        if isinstance(value, list) and not value:
            return default
        if isinstance(value, str) and not value.strip():
            return default
        return str(value)